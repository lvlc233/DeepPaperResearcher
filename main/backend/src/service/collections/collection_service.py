
from typing import List, Optional, Annotated
from uuid import UUID
from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from base.pg.service import CollectionRepository, PaperRepository, SessionDep, UserRepository
from base.pg.entity import Collection
from service.collections.schema import CollectionDTO, CollectionDetailDTO
from service.papers.schema import PaperMeta

class CollectionService:
    """
    收藏夹服务层
    """

    def __init__(self, session: AsyncSession):
        self.session = session



    async def ensure_default_collection(self, user_id: UUID) -> Collection:
        user = await UserRepository.get_user_by_id(self.session, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        default_collection = await CollectionRepository.get_default_collection(self.session, user_id)
        if default_collection:
            return default_collection

        try:
            collection = Collection(
                user_id=user_id,
                name="默认收藏夹",
                is_default=True,
            )
            return await CollectionRepository.create_collection(self.session, collection)

        except IntegrityError:
            await self.session.rollback()
            default_collection = await CollectionRepository.get_default_collection(self.session, user_id)
            if default_collection:
                return default_collection
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建默认收藏夹失败")

    async def create_collection(self, user_id: UUID, name:str) -> CollectionDTO:
        """创建收藏夹"""
        collection = Collection(
            user_id=user_id,
            name=name,
        )
        created = await CollectionRepository.create_collection(self.session, collection)
        return CollectionDTO.model_validate(created)

    async def get_user_collections(
        self, 
        user_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[CollectionDTO]:
        """获取用户收藏夹列表"""
        if offset == 0:
            await self.ensure_default_collection(user_id)
        results = await CollectionRepository.get_user_collections_with_counts(
            self.session, user_id, limit, offset
        )
        
        responses = []
        for collection, count in results:
            resp = CollectionDTO.model_validate(collection)
            resp.total = count
            responses.append(resp)
            
        return responses

    async def get_collection_details(self, collection_id: UUID, user_id: UUID) -> CollectionDetailDTO:
        """获取收藏夹详情（包含论文列表）"""
        # 1. Check collection exists and belongs to user
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏夹不存在")
        
        # 2. Fetch papers (default limit 1000 to simulate 'all')
        papers = await CollectionRepository.get_collection_papers(self.session, collection_id, limit=1000)
        
        items = []
        for p in papers:
            items.append(PaperMeta(
                paper_id=p.id,
                url=p.file_url,
                title=p.title,
                authors=p.authors if p.authors else [],
                summary=p.abstract,
                published_at=p.created_at,
                source=p.source_type or "PDF",
                tags=[], # Tags not available in Paper entity yet
                references_number=None
            ))
            
        return CollectionDetailDTO(items=items)

    async def move_paper(self, paper_id: UUID, target_collection_id: UUID, user_id: UUID) -> bool:
        """移动论文到指定收藏夹"""
        # 1. Check target collection
        target_collection = await CollectionRepository.get_collection_by_id(self.session, target_collection_id)
        if not target_collection or target_collection.user_id != user_id:
            return False 
            
        # 2. Check paper exists
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
             return False
             
        # 3. Remove from all user's collections
        await CollectionRepository.remove_paper_from_user_collections(self.session, user_id, paper_id)
        
        # 4. Add to target
        await CollectionRepository.add_paper_to_collection(self.session, target_collection_id, paper_id)
        
        return True


    async def update_collection(
        self, 
        collection_id: UUID, 
        user_id: UUID, 
        new_name: Optional[str] = None,
    ) -> Optional[CollectionDTO]:
        """更新收藏夹"""
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return None

        if collection.is_default and new_name is not None and new_name != collection.name:
            # TODO: 这里要自定义异常。这里的HTTP都要
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="默认收藏夹不允许重命名")

        if new_name is not None:
            collection.name = new_name      
        collection.updated_at = datetime.now()
        updated = await CollectionRepository.update_collection(self.session, collection)
        return CollectionDTO.model_validate(updated)

    async def delete_collection(self, collection_id: UUID, user_id: UUID) -> bool:
        """删除收藏夹"""
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False

        if collection.is_default:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="默认收藏夹不允许删除")
        # TODO: 这里有没有联表删除,就是删除该收藏夹下的论文。
        return await CollectionRepository.delete_collection(self.session, collection)

    async def add_paper_to_collection(
        self, 
        collection_id: UUID, 
        paper_id: UUID, 
        user_id: UUID
    ) -> bool:
        """添加论文到收藏夹"""
        # 1. 检查收藏夹是否存在且属于该用户
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False
            
        # 2. 检查论文是否存在
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper:
            return False
            
        # 3. 添加关联
        await CollectionRepository.add_paper_to_collection(self.session, collection_id, paper_id)
        return True

    async def remove_paper_from_collection(
        self, 
        collection_id: UUID, 
        paper_id: UUID, 
        user_id: UUID
    ) -> bool:
        """从收藏夹移除论文"""
        # 1. 检查收藏夹权限
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False
            
        return await CollectionRepository.remove_paper_from_collection(self.session, collection_id, paper_id)


def get_collection_service(session: SessionDep) -> CollectionService:
    """依赖注入工厂"""
    return CollectionService(session)

CollectionServiceDep = Annotated[CollectionService, Depends(get_collection_service)]
