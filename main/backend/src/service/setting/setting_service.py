"""
配置服务实现。

开发者: BackendAgent
当前版本: v1.1_setting_service_alignment
创建时间: 2026-01-14 19:00:00
更新时间: 2026-01-20 12:46:00
更新记录:
    [2026-01-14 19:00:00:v1.0_config_service:初始化配置服务]
    [2026-01-20 12:46:00:v1.1_setting_service_alignment:对齐统一架构 Settings 服务]

变更说明:
    注释者: BackendAgent(python)
    注释时间: 2026-01-20 12:46:00
    使用说明: Settings 服务供 /settings 模块与 Auth 响应读取用户设置
    实现概要: 基于 User.settings JSON 持久化，提供结构化读写与掩码处理
    变更原因: 以统一架构文档为标准替换旧配置服务
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.entity import User
from base.pg.service import UserRepository
from service.setting.schema import (
    AIReaderSettings,
    AISearchSettings,
    Settings,
    SourceSettings,
    SystemSettings,
)


class SettingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def _get_user(self, user_id: UUID) -> User:
        user = await UserRepository.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return user

    def _parse_source_index(self, source_id: str, total: int) -> int:
        try:
            index = int(source_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source_id无效")
        if index < 0 or index >= total:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source_id不存在")
        return index

    def _mask_api_key(self, api_key: str) -> str:
        # 掩盖API密钥,显示前4位和后4位,中间用****替换
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}****{api_key[-4:]}"

    async def _save_settings(self, user: User, settings: Settings) -> Settings:
        user.settings = settings
        await UserRepository.update_user(self.db, user)
        return settings

    async def get_settings(self, user_id: UUID) -> Settings:
        user = await self._get_user(user_id)
        if not user.settings:
             return Settings()
        return user.settings

    async def get_source_settings(self, user_id: UUID) -> List[SourceSettings]:
        settings = await self.get_settings(user_id)
        return settings.source_settings

    async def add_source_settings(self, user_id: UUID, data: SourceSettings) -> SourceSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.source_settings.append(data)
        await self._save_settings(user, settings)
        return data



    async def update_source_settings(self, user_id: UUID, source_id: str, data: SourceSettings) -> SourceSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        index = self._parse_source_index(source_id, len(settings.source_settings))
        settings.source_settings[index] = data
        await self._save_settings(user, settings)
        return data

    async def delete_source_settings(self, user_id: UUID, source_id: str) -> SourceSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        index = self._parse_source_index(source_id, len(settings.source_settings))
        removed = settings.source_settings.pop(index)
        await self._save_settings(user, settings)
        return removed

    async def get_ai_search_settings(self, user_id: UUID) -> AISearchSettings:
        settings = await self.get_settings(user_id)
        ai_settings = settings.ai_search_settings
        return AISearchSettings(
            **ai_settings.model_dump(),
            api_key=self._mask_api_key(ai_settings.api_key),
        )

    async def update_ai_search_settings(self, user_id: UUID, data: AISearchSettings) -> AISearchSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.ai_search_settings = data
        await self._save_settings(user, settings)
        return await self.get_ai_search_settings(user_id)

    async def get_ai_reader_settings(self, user_id: UUID) -> List[AIReaderSettings]:
        settings = await self.get_settings(user_id)
        masked_items: List[AIReaderSettings] = []
        for item in settings.ai_reader_settings:
            masked_items.append(
                AIReaderSettings(
                    **item.model_dump(),
                    api_key=self._mask_api_key(item.api_key),
                )
            )
        return masked_items

    async def update_ai_reader_settings(self, user_id: UUID, data: List[AIReaderSettings]) -> List[AIReaderSettings]:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.ai_reader_settings = data
        await self._save_settings(user, settings)
        return await self.get_ai_reader_settings(user_id)

    async def get_system_settings(self, user_id: UUID) -> SystemSettings:
        settings = await self.get_settings(user_id)
        return SystemSettings(**settings.system_settings.model_dump())

    async def update_system_settings(self, user_id: UUID, data: SystemSettings) -> SystemSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.system_settings.system_colour = data.system_colour
        await self._save_settings(user, settings)
        return await self.get_system_settings(user_id)
