"""
配置管理 API 路由。

开发者: BackendAgent
当前版本: v1.0_config_router
创建时间: 2026-01-14 20:30:00
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from base.pg.entity import User
from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from controller.response import Response
from controller.api.settings.schema import (
    AddSourceSettingsRequest,
    AISearchSettingsRequest,
    AISearchSettingsResponse,
    AIReaderSettingsRequest,
    AIReaderSettingsResponse,
    SourceSettingsResponse,
    SystemSettingsRequest,
    SystemSettingsResponse,
)
from service.setting.setting_service import SettingService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_setting_service(db: SessionDep) -> SettingService:
    return SettingService(db)


SettingServiceDep = Annotated[SettingService, Depends(get_setting_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

@router.get("/search/sources", response_model=Response[SourceSettingsResponse])
async def get_search_sources(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    settings = await service.get_source_settings(current_user.id)
    return Response.success(data=SourceSettingsResponse.model_validate(settings))


@router.post("/search/sources", response_model=Response)
async def add_search_source(
    data: AddSourceSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.add_source_settings(current_user.id, data)
    # 按照接口接口文档的标准,返回空对象,但保留service的返回。
    return Response.success()


@router.patch("/search/sources/{source_id}", response_model=Response)
async def update_search_source(
    source_id: str,
    data: AddSourceSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.update_source_settings(current_user.id, source_id, data)
    return Response.success()


@router.delete("/search/sources/{source_id}", response_model=Response)
async def delete_search_source(
    source_id: str,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.delete_source_settings(current_user.id, source_id)
    return Response.success()


@router.get("/search/ai", response_model=Response[AISearchSettingsResponse])
async def get_ai_search_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    settings = await service.get_ai_search_settings(current_user.id)
    return Response.success(data=AISearchSettingsResponse.model_validate(settings))


@router.put("/search/ai", response_model=Response)
async def update_ai_search_settings(
    data: AISearchSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.update_ai_search_settings(current_user.id, data)
    return Response.success()


@router.get("/reader/ai", response_model=Response[AIReaderSettingsResponse])
async def get_ai_reader_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    settings = await service.get_ai_reader_settings(current_user.id)
    return Response.success(data=AIReaderSettingsResponse.model_validate(settings))


@router.put("/reader/ai", response_model=Response)
async def update_ai_reader_settings(
    data: AIReaderSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.update_ai_reader_settings(current_user.id, data)
    return Response.success()


@router.get("/system", response_model=Response[SystemSettingsResponse])
async def get_system_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    settings = await service.get_system_settings(current_user.id)
    return Response.success(data=SystemSettingsResponse.model_validate(settings))


@router.put("/system", response_model=Response)
async def update_system_settings(
    data: SystemSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    await service.update_system_settings(current_user.id, data)
    return Response.success()
