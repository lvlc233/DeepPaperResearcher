'''
开发者: BackendAgent
当前版本: v1.1_security
创建时间: 2026-01-12 12:45:00
更新时间: 2026-01-20 10:35:00
更新记录: 
    [2026-01-12 12:45:00:v1.0_security:创建密码哈希与JWT工具]
    [2026-01-20 10:35:00:v1.1_security:补充Refresh Token生成与解析能力]
'''
from datetime import datetime, timedelta
from typing import Optional, Any, Union
import jwt
from passlib.context import CryptContext
from base.config import settings
from loguru import logger
# 安全相关的工具。


# 密码哈希上下文
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    """
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        subject: 令牌主题 (通常是 user_id 或 email)
        expires_delta: 过期时间差
        
    Returns:
        str: JWT Token
    """
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 刷新令牌
    
    Args:
        subject: 令牌主题 (通常是 user_id 或 email)
        expires_delta: 过期时间差
        
    Returns:
        str: JWT Token
    """
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=settings.jwt_refresh_expiration_days)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 访问令牌
    
    Args:
        token: JWT Token
        
    Returns:
        dict: 解码后的 Payload，如果失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def decode_refresh_token(token: str) -> Optional[dict]:
    """
    解码 JWT 刷新令牌
    
    Args:
        token: JWT Token
        
    Returns:
        dict: 解码后的 Payload，如果失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

