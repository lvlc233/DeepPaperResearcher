'''
开发者: BackendAgent
当前版本: v1.0_enums
创建时间: 2026年01月10日 10:00
更新时间: 2026年01月10日 10:00
更新记录:
    [2026年01月10日 10:00:v1.0_enums:从entity.py提取PaperStatus枚举，解耦数据模型]
'''

from enum import Enum

class PaperStatus(str, Enum):
    """论文处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
