from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from common.model.enums import PaperStatus
from service.papers.schema import PaperDTO, PaperMeta


class SearchFilter(BaseModel):
    """搜索过滤条件"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    authors: Optional[List[str]] = Field(None, description="作者列表")
    status: Optional[PaperStatus] = Field(None, description="论文状态")
    source: Optional[str] = Field(None, description="搜索来源(local/arXiv), 默认为local")


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索关键词", min_length=1)
    filters: Optional[SearchFilter] = Field(None, description="过滤条件")
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(10, ge=1, le=100, alias="page_size", description="每页数量")
    enable_semantic_search: bool = Field(False, description="是否启用语义搜索(暂未实现)")


class SearchedPaperMetaResponse(BaseModel):
    """搜索结果响应 (Standardized)"""
    items: List[PaperMeta]
    total: int
    query_id: Optional[UUID] = Field(None, description="搜索历史记录ID")


class SearchHistoryResponse(BaseModel):
    """搜索历史响应"""
    id: UUID
    query: str
    created_at: datetime
    result_count: int

class SearchResponse(BaseModel):
    """搜索结果响应"""
    total: int
    items: List[PaperDTO]
    query_id: Optional[UUID] = Field(None, description="搜索历史记录ID")


class SearchSettingsResponse(BaseModel):
    """搜索配置响应 (聚合了 search.* 和 agent.search_depth)"""
    enable_deep_reasoning: bool = Field(False, description="是否开启深度推理")
    enable_auto_summary: bool = Field(True, description="是否自动生成摘要")
    default_sort_by: str = Field("relevance", description="默认排序方式")
    max_results: int = Field(10, description="默认每页数量")
    search_depth: int = Field(3, description="搜索深度")


class SearchSettingsUpdate(BaseModel):
    """搜索配置更新"""
    enable_deep_reasoning: Optional[bool] = None
    enable_auto_summary: Optional[bool] = None
    default_sort_by: Optional[str] = None
    max_results: Optional[int] = None
    search_depth: Optional[int] = None
