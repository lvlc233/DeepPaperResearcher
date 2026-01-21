from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlmodel import Session

from base.redis.service import get_redis
from base.pg.service import get_db_session
from service.setting.setting_service import SettingService
from controller.api.search.schema import (
    SearchRequest, 
    SearchResponse, 
    SearchHistoryResponse,
    SearchSettingsResponse,
    SearchSettingsUpdate,
    SearchedPaperMetaResponse
)
from service.search.search_service import SearchService, get_search_service
from controller.api.auth.router import get_current_user
from controller.response import Response
from base.pg.entity import User
from base.arxiv.client import ArxivClient
from base.arxiv.parser import ArxivXmlParser
from service.papers.arxiv_service import ArxivService

router = APIRouter(prefix="/search", tags=["Search"])

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

def get_arxiv_service():
    return ArxivService(ArxivClient(), ArxivXmlParser())

# TODO: 或可以把AI搜索和普通搜索分成两个?这样子,普通搜索也可以利用embadding进行语义搜索了。
@router.post("", response_model=Response[SearchedPaperMetaResponse])
async def search_papers(
    request: SearchRequest,
    current_user: CurrentUserDep,
    search_service: SearchServiceDep
):
    """
    搜索论文
    - 支持关键词匹配 (title, abstract)
    - 支持过滤 (日期, 状态)
    - 自动记录搜索历史
    """
    arxiv_service = get_arxiv_service()
    result = await search_service.search_papers(current_user.id, request, arxiv_service)
    return Response.success(data=result)

@router.get("/history", response_model=Response[List[SearchHistoryResponse]])
async def get_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep,
    limit: int = Query(10, ge=1, le=50)
):
    """获取最近搜索历史"""
    history = await search_service.get_search_history(current_user.id, limit)
    return Response.success(data=history)

@router.delete("/history", response_model=Response[bool])
async def clear_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep
):
    """清空搜索历史"""
    await search_service.clear_search_history(current_user.id)
    return Response.success(data=True)


from service.setting.setting_service import SettingService

def get_setting_service(
    db: Session = Depends(get_db_session),
) -> SettingService:
    return SettingService(db)

@router.get("/config", response_model=Response[SearchSettingsResponse])
async def get_search_config(
    current_user: CurrentUserDep,
    setting_service: SettingService = Depends(get_setting_service)
):
    """获取搜索相关配置"""
    settings = await setting_service.get_settings(current_user.id)
    ai_search = settings.ai_search_settings
    
    return Response.success(
        data=SearchSettingsResponse(
        enable_deep_reasoning=ai_search.search_deep == "deep",
        enable_auto_summary=ai_search.ai_summary_enable,
        default_sort_by=ai_search.search_preferences,
        max_results=ai_search.search_limit,
        search_depth=ai_search.search_loop
    ))


@router.put("/config", response_model=Response[SearchSettingsResponse])
async def update_search_config(
    data: SearchSettingsUpdate,
    current_user: CurrentUserDep,
    setting_service: SettingService = Depends(get_setting_service)
):
    """更新搜索相关配置"""
    settings = await setting_service.get_settings(current_user.id)
    ai_search = settings.ai_search_settings

    if data.enable_deep_reasoning is not None:
        ai_search.search_deep = "deep" if data.enable_deep_reasoning else "standard"
    if data.enable_auto_summary is not None:
        ai_search.ai_summary_enable = data.enable_auto_summary
    if data.default_sort_by is not None:
        # 简单映射，假设前端传递的值是合法的
        ai_search.search_preferences = data.default_sort_by # type: ignore
    if data.max_results is not None:
        ai_search.search_limit = data.max_results
    if data.search_depth is not None:
        ai_search.search_loop = data.search_depth

    # 保存
    settings.ai_search_settings = ai_search
    await setting_service._save_settings(await setting_service._get_user(current_user.id), settings)

    return Response.success(
        data=SearchSettingsResponse(
        enable_deep_reasoning=ai_search.search_deep == "deep",
        enable_auto_summary=ai_search.ai_summary_enable,
        default_sort_by=ai_search.search_preferences,
        max_results=ai_search.search_limit,
        search_depth=ai_search.search_loop
    ))
