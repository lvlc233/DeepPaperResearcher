"""
开发者: BackendAgent(python)
当前版本: v1.2_settings_schema_alignment
创建时间: 2026-01-14 19:20:00
更新时间: 2026-01-20 12:46:00
更新记录:
    [2026-01-14 19:20:00:v1.0_config_schema:初始化配置读取与更新模型]
    [2026-01-20 12:25:00:v1.1_config_schema:补充Settings模型供认证响应复用]
    [2026-01-20 12:46:00:v1.2_settings_schema_alignment:对齐统一架构 Settings 模型]

变更说明:
    注释者: BackendAgent(python)
    注释时间: 2026-01-20 12:46:00
    使用说明: 供 /settings 模块接口与 Auth 响应复用
    实现概要: 定义搜索来源、AI 搜索/阅读、系统设置等结构化 DTO
    变更原因: 以统一架构文档为标准替换旧配置模型
"""

from datetime import date
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceSettings(BaseModel):
    name: str
    type: Literal["web", "local"]
    source: str # url or collection_id
    enable: bool = True

class AISearchSettings(BaseModel):
    llm_name: str = "" # 模型名称
    provider: str = "" # 模型供应商
    api_key: str = "" # 模型API密钥
    base_url: str = "" # 模型API base_url
    search_limit: int = 10 # 搜索限制
    search_loop: int = 3 # 搜索循环次数
    ai_summary_enable: bool = True # 是否启用AI摘要
    search_deep: Literal["shallow", "standard", "deep"] = "standard" # 搜索深度
    search_preferences: Literal["latest", "relevant", "mixed"] = "mixed" # 搜索偏好
    search_date_max: date = Field(default_factory=date.today) # 搜索日期最大值
    search_date_min: date = Field(default_factory=date.today) # 搜索日期最小值

class AIReaderSettings(BaseModel):
    type: Literal["deep_research", "chat", "summary", "mind_map"]  # 配置类型 :[深度研究,chat,总结,脑图]
    llm_name: str = ""  # 模型名称
    provider: str = ""  # 模型供应商
    api_key: str = ""  # 模型API密钥
    base_url: str = ""  # 模型API base_url
    config: Dict[str, Any] = Field(default_factory=dict) # 阅读配置

class SystemSettings(BaseModel):
    system_colour: Literal["light", "dark"] = "light"



class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_settings: List[SourceSettings] = Field(default_factory=list)
    ai_search_settings: AISearchSettings = Field(default_factory=AISearchSettings)
    ai_reader_settings: List[AIReaderSettings] = Field(default_factory=list)
    system_settings: SystemSettings = Field(default_factory=SystemSettings)
