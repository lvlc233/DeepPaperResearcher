"""
开发者: BackendAgent(python)
当前版本: v1.2_auth_schema
创建时间: 2026-01-12 13:10:00
更新时间: 2026-01-20 12:25:00
更新记录:
    [2026-01-12 13:10:00:v1.0_auth_schema:初始化认证请求与响应模型]
    [2026-01-20 10:35:00:v1.1_auth_schema:对齐Auth模块请求响应模型与TokenPair刷新结构]
    [2026-01-20 12:25:00:v1.2_auth_schema:复用Settings模型并清理Auth内设置定义]
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from service.setting.schema import Settings
from base.pg.entity import User

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    settings: Settings


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    settings: Settings
    access_token: str
    refresh_token: Optional[str] = None

"""
转换函数
"""
def _build_user_public_response(user: User) -> UserPublicResponse:
    settings_data = user.settings
    settings = Settings.model_validate(settings_data)
    return UserPublicResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        is_active=user.is_active,
        created_at=user.created_at,
        settings=settings,
    )

def _build_login_response(user: User, access_token: str, refresh_token: Optional[str]) -> LoginResponse:
    user_response = _build_user_public_response(user)
    payload = user_response.model_dump()
    return LoginResponse(
        **payload,
        access_token=access_token,
        refresh_token=refresh_token,
    )