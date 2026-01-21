import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_

from fastapi import Depends, HTTPException, status

from base.pg.service import SessionDep
from base.pg.entity import Paper, PaperChunk, SearchHistory, User
from controller.api.search.schema import SearchRequest, SearchFilter, SearchResponse, SearchedPaperMetaResponse
from service.papers.schema import PaperMeta
from service.papers.paper_service import PaperServiceDep
from service.papers.arxiv_service import ArxivService
from common.model.enums import PaperStatus

logger = logging.getLogger(__name__)
# TODO: 相关说明已经在schema中标注了。
class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本向量 (Mock)
        TODO: 对接真实 Embedding 服务
        """
        import random
        # 1536 dim for OpenAI compatibility
        return [random.random() for _ in range(1536)]

    async def search_papers(
        self, 
        user_id: UUID, 
        request: SearchRequest,
        arxiv_service: Optional[ArxivService] = None
    ) -> SearchedPaperMetaResponse:
        """
        执行论文搜索
        支持文本匹配和语义搜索
        支持本地搜索和外部源搜索(arXiv)
        """
        logger.info(f"Processing search request. User: {user_id}, Query: '{request.query}', Filters: {request.filters}")

        # 0. 检查是否为外部源搜索
        is_external = False
        if request.filters and request.filters.source and request.filters.source.lower() == 'arxiv':
            is_external = True
            
        if is_external and arxiv_service and request.query:
            logger.info("Executing external search (Arxiv) as requested.")
            return await self._search_external(user_id, request, arxiv_service)

        # 1. 本地搜索 - 构建基础查询
        logger.info("Executing local search.")
        query = select(Paper).where(
            Paper.user_id == user_id,
            Paper.status != PaperStatus.FAILED
        )

        # 2. 语义搜索或关键词匹配
        if request.enable_semantic_search and request.query:
            embedding = await self._get_embedding(request.query)
            # 语义搜索: 查找最相似的 Chunk 所属的 Paper
            # 注意: 这里逻辑简化，直接 Join 并按距离排序
            # 真实场景可能需要先筛选 Chunk 再聚合 Paper
            query = query.join(PaperChunk).order_by(
                PaperChunk.embedding.cosine_distance(embedding)
            )
            # 由于一对多，需要去重。但 distinct 与 order_by 冲突处理较麻烦
            # 这里简单处理: 不去重，直接返回 Chunk 对应的 Paper (可能会有重复)，
            # 或者在应用层去重。
            # 为了演示，我们假设只返回最相关的一个 Chunk 对应的 Paper 列表 (可能会重复)
            # 更好的做法是 subquery
        elif request.query:
            # 关键词匹配
            search_term = f"%{request.query}%"
            query = query.where(
                or_(
                    Paper.title.ilike(search_term),
                    Paper.abstract.ilike(search_term)
                )
            )
            query = query.order_by(desc(Paper.created_at))
        else:
             # 无关键词，默认按时间倒序
             query = query.order_by(desc(Paper.created_at))

        # 3. 应用高级过滤器 (Common)
        if request.filters:
            if request.filters.start_date:
                query = query.where(Paper.created_at >= request.filters.start_date)
            if request.filters.end_date:
                query = query.where(Paper.created_at <= request.filters.end_date)
            if request.filters.status:
                query = query.where(Paper.status == request.filters.status)

        # 4. 计算总数 (Simplified for semantic search performance)
        # count_stmt = select(func.count()).select_from(query.subquery())
        # total = (await self.session.execute(count_stmt)).scalar_one()
        # 暂且简单处理 total，如果是语义搜索，total 可能不准确或者是 limit
        total = 0 
        
        # 5. 分页与执行
        if not request.enable_semantic_search:
             # 非语义搜索计算 Total
             count_stmt = select(func.count()).select_from(query.subquery())
             total = (await self.session.execute(count_stmt)).scalar_one()
             
             query = query.offset((request.page - 1) * request.limit).limit(request.limit)
             result = await self.session.execute(query)
             papers = result.scalars().all()
        else:
             # 语义搜索分页
             # 直接 limit (语义搜索通常是 TopK)
             query = query.limit(request.limit).offset((request.page - 1) * request.limit)
             result = await self.session.execute(query)
             papers = result.scalars().all()
             # 去重 (保持顺序)
             seen = set()
             unique_papers = []
             for p in papers:
                 if p.id not in seen:
                     unique_papers.append(p)
                     seen.add(p.id)
             papers = unique_papers
             total = len(papers) # Mock total for semantic search

        # 6. 记录搜索历史
        query_id = await self._save_search_history(user_id, request, total)

        # 转换 convert to PaperMeta
        items = []
        for p in papers:
            items.append(PaperMeta(
                paper_id=p.id,
                url=None, # TODO: generate url
                title=p.title,
                authors=p.authors if p.authors else [],
                summary=p.abstract,
                published_at=p.created_at,
                source='local',
                tags=[],
                references_number=None
            ))

        # Fallback to Arxiv if local search is empty and source is not explicitly 'local'
        if total == 0 and (not request.filters or not request.filters.source) and arxiv_service and request.query:
            logger.info("Local search returned 0 results and source not strictly 'local'. Falling back to Arxiv.")
            return await self._search_external(user_id, request, arxiv_service)

        return SearchedPaperMetaResponse(
            total=total,
            items=items,
            query_id=query_id
        )

    async def _search_external(self, user_id: UUID, request: SearchRequest, arxiv_service: ArxivService) -> SearchedPaperMetaResponse:
        """Helper method for external search"""
        start = (request.page - 1) * request.limit
        results = await arxiv_service.search_papers(request.query, start=start, max_results=request.limit)
        
        items = []
        for p in results:
                items.append(PaperMeta(
                    paper_id=None, 
                    url=p.pdf_url,
                    title=p.title,
                    authors=p.authors,
                    summary=p.abstract,
                    published_at=p.published_date,
                    source='arXiv',
                    tags=p.categories,
                    references_number=None
                ))
        
        # 记录历史
        await self._save_search_history(user_id, request, len(items))
        
        return SearchedPaperMetaResponse(
            items=items,
            total=len(items),
            query_id=None 
        )

    async def _save_search_history(self, user_id: UUID, request: SearchRequest, total: int) -> Optional[UUID]:
        try:
            history = SearchHistory(
                user_id=user_id,
                session_name=request.query, # Map query to session_name
                filters=request.filters.model_dump() if request.filters else None,
                result_count=total
            )
            self.session.add(history)
            await self.session.commit()
            await self.session.refresh(history)
            return history.id
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            return None

    async def get_search_history(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[SearchHistory]:
        """获取最近搜索历史"""
        stmt = select(SearchHistory).where(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def clear_search_history(self, user_id: UUID) -> int:
        """清空搜索历史"""
        # delete 语句
        from sqlalchemy import delete
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


async def get_search_service(session: SessionDep) -> SearchService:
    return SearchService(session)
