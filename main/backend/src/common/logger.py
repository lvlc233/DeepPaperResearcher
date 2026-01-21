import logging
import sys
from types import FrameType
from typing import cast

from loguru import logger
from common.model.errors import BaseAppException

# TODO: 这个是?怎么用的?
class InterceptHandler(logging.Handler):
    """
    拦截标准logging消息并重定向到Loguru
    """
    def emit(self, record: logging.LogRecord) -> None:
        # 获取对应的Loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # 查找调用者的帧，以便Loguru可以报告正确的位置
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        # 如果是自定义业务异常，不打印堆栈信息
        exc_info = record.exc_info
        if exc_info and isinstance(exc_info[1], BaseAppException):
            exc_info = None

        logger.opt(depth=depth, exception=exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """
    配置Loguru并拦截标准logging
    """
    # 移除Loguru默认的handler
    logger.remove()
    
    # 添加新的handler，输出到stderr
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 拦截标准logging模块的日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 强制将Uvicorn和FastAPI的logger重定向
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    logger.info("日志系统初始化完成 (Loguru)")
