"""
开发者: BackendAgent
创建时间: 2026年01月10日
描述: 自定义异常类定义
"""

from typing import Any, Optional

class BaseAppException(Exception):
    """应用基础异常类"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

class BusinessError(BaseAppException):
    """业务逻辑错误 (默认 400)"""
    def __init__(self, message: str = "业务处理失败", code: int = 400, data: Any = None):
        super().__init__(code, message, data)

class AuthenticationError(BaseAppException):
    """认证失败 (默认 401)"""
    def __init__(self, message: str = "未授权访问", code: int = 401, data: Any = None):
        super().__init__(code, message, data)

class PermissionError(BaseAppException):
    """权限不足 (默认 403)"""
    def __init__(self, message: str = "权限不足", code: int = 403, data: Any = None):
        super().__init__(code, message, data)

class NotFoundError(BaseAppException):
    """资源未找到 (默认 404)"""
    def __init__(self, message: str = "资源未找到", code: int = 404, data: Any = None):
        super().__init__(code, message, data)

class SystemError(BaseAppException):
    """系统内部错误 (默认 500)"""
    def __init__(self, message: str = "系统内部错误", code: int = 500, data: Any = None):
        super().__init__(code, message, data)
