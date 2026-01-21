'''
开发者: BackendAgent
当前版本: v1.4_auth_refresh_alignment
创建时间: 2026-01-12 13:15:00
更新时间: 2026-01-20 12:25:00
更新记录: 
    [2026-01-12 13:15:00:v1.0_auth_router:实现真实的认证路由，接入AuthService和JWT]
    [2026-01-17 22:44:00:v1.1_auth_cookie_fallback:认证依赖支持从Cookie读取access_token，兼容浏览器直接打开PDF资源]
    [2026-01-17 23:11:00:v1.2_auth_login_set_cookie_response:登录接口改为显式 JSONResponse 设置 cookie，避免 Set-Cookie 丢失]
    [2026-01-20 10:35:00:v1.3_auth_refresh_alignment:对齐认证响应模型并新增refresh接口]
    [2026-01-20 12:25:00:v1.4_auth_refresh_alignment:对齐Settings模型引用来源]
'''
# 主要就是生成一个jwt

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from base.config import settings
from base.pg.entity import User
from service.auth.auth_service import AuthServiceDep
from common.security import create_access_token, create_refresh_token
from controller.response import Response
from controller.api.auth.schema import (
    RegisterRequest,
    LoginRequest,
    UserPublicResponse,
    LoginResponse,
    TokenPairResponse,
    _build_login_response,
    _build_user_public_response
)


router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])

# OAuth2 Scheme
# 笔记: 这个可以获取请求头中的Authorization字段,简单来说就是获取token 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)



# 笔记: 这个函数就是从请求头中获取token,如果没有,就从cookie中获取,如果还是没有,就抛出异常。
# 鉴权:其他需要鉴权的controller接口都需要注入这个controller,不论是否需要user信息。
# 这个接口去service层解析token,service验证token是否有效,如果有效,就返回user信息。
async def get_current_user(
    request: Request,
    service: AuthServiceDep,
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    query_token: Annotated[Optional[str], Query(alias="token")] = None,
) -> User:
    """
    获取当前登录用户 (Dependency)
    鉴权顺序: Header (Bearer) -> Query Param (?token=) -> Cookie (access_token)
    
    Logic delegated to AuthService.
    """
    resolved_token = token or query_token or request.cookies.get("access_token")

    if not resolved_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # 这里会解析jwt和从数据库中获取用户信息。
    return await service.get_user_by_token(resolved_token)

# TODO: 接入第三方登录 (Google/GitHub), 计划单独开设 /auth/oauth/{provider} 接口


@router.post("/login", response_model=Response[LoginResponse])
async def login(
    form_data: LoginRequest,
    service: AuthServiceDep
):
    """
    用户登录
    """
   
    user = await service.authenticate_user(form_data.email, form_data.password)
    
    # 生成 Token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id) if form_data.remember_me else None

    payload = Response.success(
        data=_build_login_response(user, access_token, refresh_token)
    ).model_dump(mode="json")

    resp = JSONResponse(status_code=status.HTTP_200_OK, content=payload)
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expiration_minutes * 60,
        path="/",
    )

    return resp

# ok
@router.post("/register", response_model=Response[UserPublicResponse])
async def register(
    user_in: RegisterRequest,
    service: AuthServiceDep
):
    """
    用户注册
    """
    # 失败会抛出 BusinessError

    user = await service.create_user(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name
    )
    
    return Response.success(data=_build_user_public_response(user))

@router.get("/refresh", response_model=Response[TokenPairResponse])
async def refresh_token(
    service: AuthServiceDep,
    refresh_token: str = Query(...)
):
    user = await service.get_user_by_refresh_token(refresh_token)
    access_token = create_access_token(subject=user.id)
    refresh_token_value = create_refresh_token(subject=user.id)

    payload = Response.success(
        data=TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token_value,
        )
    ).model_dump(mode="json")

    resp = JSONResponse(status_code=status.HTTP_200_OK, content=payload)
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expiration_minutes * 60,
        path="/",
    )

    return resp
