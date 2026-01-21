from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from service.papers.schema import PaperMeta


class CollectionResponse(BaseModel):
    """收藏夹响应模型"""
    name: str = Field(..., description="收藏夹名称")
    id: UUID = Field(..., alias="collection_id", description="收藏夹ID")
    user_id: UUID = Field(..., description="所属用户ID")
    is_default: bool = Field(False, description="是否为默认收藏夹")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    total: int = Field(0, description="收藏夹下的论文数量")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class CollectionDetailResponse(BaseModel):
    """收藏夹详情响应"""
    items: List[PaperMeta]

class CreateCollectionRequest(BaseModel):
    name: str = Field(..., description="收藏夹名称")
