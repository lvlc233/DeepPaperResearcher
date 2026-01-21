# 工具函数
# 定义一些常用的工具函数，如时间格式化、字符串处理等。

from datetime import datetime
from zoneinfo import ZoneInfo

"""
在应用层统一用 UTC 时间
仅在展示时转换为本地时区
"""
# 获取上海时间
def get_now_time_china():
    return datetime.now(ZoneInfo("Asia/Shanghai"))
def format_time_china(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S %z') 
