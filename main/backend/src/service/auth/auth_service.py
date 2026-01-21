'''
开发者: BackendAgent
当前版本: v1.1_auth_service
创建时间: 2026-01-12 13:00:00
更新时间: 2026-01-20 10:35:00
更新记录: 
    [2026-01-12 13:00:00:v1.0_auth_service:创建认证服务，实现登录、注册逻辑]
    [2026-01-20 10:35:00:v1.1_auth_service:补充Refresh Token校验获取用户逻辑]
'''

from uuid import UUID
from typing import Optional, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from base.pg.entity import User, Collection
from base.pg.service import UserRepository, CollectionRepository
from common.security import get_password_hash, verify_password, decode_access_token, decode_refresh_token
from common.logger import logger
from common.model.errors import AuthenticationError, BusinessError, NotFoundError

from base.pg.service import SessionDep
# 这里就直接返回User吧,权限特殊点。

class AuthService:
    """
    认证服务
    
    负责处理用户登录、注册、密码验证等业务逻辑。

    TODO:
        - 增加密码重置功能
        - 支持多因素认证OAuth2.0
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    # 用于登录
    async def authenticate_user(self, email: str, password: str) -> User:
        """
        验证用户登录
        
        Args:
            email: 用户邮箱
            password: 明文密码
            
        Returns:
            User: 验证通过返回用户对象
            
        Raises:
            AuthenticationError: 认证失败
        """
        user = await UserRepository.get_user_by_email(self.session, email)
        if not user:
            logger.warning(f"登录失败: 用户不存在 {email}")
            raise AuthenticationError(message="Incorrect email or password")
            
        if not verify_password(password, user.hashed_password):
            logger.warning(f"登录失败: 密码错误 {email}")
            raise AuthenticationError(message="Incorrect email or password")
            
        if not user.is_active:
            logger.warning(f"登录失败: 账号已禁用 {email}")
            raise AuthenticationError(message="Inactive user")
            
        return user
    # 用于注册
    async def create_user(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        """
        创建新用户
        
        Args:
            email: 邮箱
            password: 密码
            full_name: 全名
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            BusinessError: 如果邮箱已存在
        """
        # 检查邮箱是否已存在
        existing_user = await UserRepository.get_user_by_email(self.session, email)
        if existing_user:
            raise BusinessError(f"邮箱 {email} 已被注册")
            
        # 创建用户实体
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True
        )
        
        # 保存到数据库
        created_user = await UserRepository.create_user(self.session, new_user)

        default_collection = Collection(
            user_id=created_user.id,
            name="默认收藏夹",
            description="系统默认收藏夹",
            is_default=True,
        )
        await CollectionRepository.create_collection(self.session, default_collection)
        logger.info(f"新用户注册成功: {email}")
        return created_user

    # 下面的用于权限验证。
    async def get_user(self, user_id: UUID) -> User:
        """根据ID获取用户"""
        user = await UserRepository.get_user_by_id(self.session, user_id)
        if not user:
             raise NotFoundError(message="User not found")
        return user

    async def get_user_by_token(self, token: str) -> User:
        """
        通过 JWT Token 获取当前用户
        (用于 Dependency)
        
        Args:
            token: JWT Token字符串
            
        Returns:
            User: 当前登录用户
            
        Raises:
            AuthenticationError: Token 无效或过期
            NotFoundError: 用户不存在
        """
        # JWT解码
        payload = decode_access_token(token)
        if payload is None:
            raise AuthenticationError(message="Could not validate credentials")

        if payload.get("type") == "refresh":
            raise AuthenticationError(message="Invalid token type")
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
             raise AuthenticationError(message="Token missing subject")

        try:
            user_id = UUID(user_id_str)
        except ValueError:
             raise AuthenticationError(message="Invalid user ID in token")

        user = await self.get_user(user_id) # Will raise NotFoundError if missing
        
        if not user.is_active:
            raise AuthenticationError(message="Inactive user")
            
        return user

    async def get_user_by_refresh_token(self, token: str) -> User:
        """
        通过 Refresh Token 获取当前用户->用于获取user_id,然后生成新的access_token
        (用于 Dependency)
        
        Args:
            token: Refresh Token字符串
            
        Returns:
            User: 当前登录用户
            
        Raises:
            AuthenticationError: Token 无效或过期
            NotFoundError: 用户不存在
        """
        # 解码token
        payload = decode_refresh_token(token)
        if payload is None:
            raise AuthenticationError(message="Could not validate refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError(message="Invalid token type")

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise AuthenticationError(message="Token missing subject")

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise AuthenticationError(message="Invalid user ID in token")

        user = await self.get_user(user_id)
        if not user.is_active:
            raise AuthenticationError(message="Inactive user")

        return user


async def get_auth_service(session: SessionDep) -> AuthService:
    """获取 AuthService 实例"""
    return AuthService(session)
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
