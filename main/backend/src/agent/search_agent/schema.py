"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:25
更新时间: 2026-01-08 18:25
更新记录: 
    [2026-01-08 18:25:v1.0.0:定义 SearchAgentState,继承 BaseAgentState,增加 search_query 和 search_results 字段]
"""

from datetime import date
from typing import Annotated, List, Optional, Dict, Any, TypedDict, Literal
from uuid import UUID
from ..base.state import BaseAgentState
from langchain_core.documents import Document

from agent.common.schema import BaseRuntimeWithModelConfig



class SearchAgentState(BaseAgentState):
    """
    SearchAgent 的专用状态定义。
    """
    
    # 经过 LLM 优化后的搜索查询语句
    search_query: Optional[str]
    # 检索到的论文
    searched_space: Optional[List[Document]] = None
    # 通过 LLM 评分后的论文列表
    rated_papers: Optional[List['SearchResponseStruct']] = None

# TODO: 我觉得配置这里,可以分为两层,一层是持久化配置(意思就是说,用户输入的配置首先进行保存,在servcie层从sql中读取配置,再将配置输入到runtime),
# TODO: 一层是运行时配置,也就是这里,Langgraph天生的RuntimeConfig,这样子也方面测试,要是其他模块要用到Agent。独立的传入运行时即可。
class SearchAgentRuntimeContext(TypedDict):
    llm_config: BaseRuntimeWithModelConfig #模型配置
    search_quantity: int = 5 # 搜索数量
    search_deep: Literal[1,2,3] = 3 # 搜索深度 (基本分别是从标题,摘要,再到内容这样子的)
    max_search_loop: int = 3 # 最大的搜索循环次数
    is_summery: bool = True # 是否开启摘要
    # TODO: 这里或许应该用数据字典。
    rating_preferences: Literal["default", "high_quality", "balanced"] = "default" # 评分偏好
    search_data_max: date
    search_data_min: date
    is_include_local: bool = True # 是否包含本地数据库中的论文
    web_url_dict: Dict[str, str] = {} # 网络搜索的url字典,key是名字,value是搜索的base_url->例如arxiv的base_url...
    # is_cache: bool = True # 是否开启缓存 

class SearchResponseStruct(TypedDict):
    """
    搜索响应的结构定义。
    """
    paper_id: UUID
    score: float
    #TODO: 得想想怎么根据上面的配置去控制结构化输出的内容。
    summary: Optional[str] = None
    