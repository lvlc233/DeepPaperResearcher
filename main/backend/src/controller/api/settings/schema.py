from datetime import date
from typing import  List, Literal

from pydantic import BaseModel, Field

from service.setting.schema import SourceSettings,AIReaderSettings

class AddSourceSettingsRequest(BaseModel):
    name: str
    type: Literal["web", "local"]
    source: str
    enable: bool = True


class SourceSettingsResponse(BaseModel):
    items: List[SourceSettings]


class AISearchSettingsRequest(BaseModel):
    llm_name: str # 大模型名称
    provider: str # 大模型供应商
    api_key: str # 大模型API密钥
    base_url: str # 大模型API base_url
    search_limit: int # 搜索限制
    search_loop: int # 搜索循环次数
    ai_summary_enable: bool # 是否启用AI摘要
    search_deep: Literal["shallow", "standard", "deep"] # 搜索深度
    search_preferences: Literal["latest", "relevant", "mixed"] # 搜索偏好
    search_date_max: date # 搜索日期最大值
    search_date_min: date # 搜索日期最小值


class AISearchSettingsResponse(BaseModel):
    llm_name: str # 大模型名称
    provider: str # 大模型供应商
    api_key: str # 大模型API密钥 加密后的
    base_url: str # 大模型API base_url
    search_limit: int # 搜索限制
    search_loop: int # 搜索循环次数
    ai_summary_enable: bool # 是否启用AI摘要
    search_deep: Literal["shallow", "standard", "deep"] # 搜索深度
    search_preferences: Literal["latest", "relevant", "mixed"] # 搜索偏好
    search_date_max: date # 搜索日期最大值
    search_date_min: date # 搜索日期最小值

class AIReaderSettingsRequest(BaseModel):
    items: List[AIReaderSettings]


class AIReaderSettingsResponse(BaseModel):
    items: List[AIReaderSettings]

class SystemSettingsRequest(BaseModel):
    system_colour: Literal["light", "dark"]


class SystemSettingsResponse(BaseModel):
    system_colour: Literal["light", "dark"]

