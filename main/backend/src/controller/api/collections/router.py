
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from controller.api.collections.schema import (
    CollectionResponse,
    CreateCollectionRequest,
    CollectionDetailResponse
)
from service.collections.collection_service import CollectionServiceDep
from controller.api.auth.router import get_current_user
from controller.response import Response
from base.pg.entity import User

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=Response[CollectionResponse])
async def create_collection(
    request: CreateCollectionRequest,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """创建收藏夹"""
    collection = await service.create_collection(current_user.id, request.name)
    return Response.success(CollectionResponse.model_validate(collection))


@router.get("", response_model=Response[List[CollectionResponse]])
async def get_collections(
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """获取我的收藏夹列表"""
    collections = await service.get_user_collections(current_user.id, limit, offset)
    cr = []
    for c in collections:
        cr.append(CollectionResponse.model_validate(c))

    return Response.success(data=cr)


@router.get("/{collection_id}", response_model=Response[CollectionDetailResponse])
async def get_collection_detail(
    collection_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取指定收藏夹的详情"""
    result = await service.get_collection_details(collection_id, current_user.id)
    return Response.success(data=result)


@router.patch("/{collection_id}", response_model=Response[CollectionResponse])
async def update_collection(
    collection_id: UUID,
    new_name: str,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """更新收藏夹信息"""
    updated = await service.update_collection(collection_id, current_user.id, new_name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏夹不存在")
    return Response.success(CollectionResponse.model_validate(updated))

@router.delete("/{collection_id}", response_model=Response[bool])
async def delete_collection(
    collection_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """删除收藏夹"""
    await service.delete_collection(collection_id, current_user.id)
    return Response.success()


@router.patch("/{collection_id}/papers/move/{paper_id}", response_model=Response[bool])
async def move_paper_to_collection(
    collection_id: UUID,
    paper_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """迁移论文到指定收藏夹"""
    success = await service.move_paper(paper_id, collection_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="移动失败：论文不存在、目标收藏夹不存在或无权访问"
        )
    return Response.success(data=True)


@router.delete("/{collection_id}/papers/{paper_id}", response_model=Response[bool])
async def remove_paper_from_collection(
    collection_id: UUID,
    paper_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """从收藏夹移除论文"""
    await service.remove_paper_from_collection(collection_id, paper_id, current_user.id)

    return Response.success()
