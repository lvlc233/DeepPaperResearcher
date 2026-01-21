# 通用的Agent数据结构(包括runtime,State,struct...)



from typing import TypedDict

# TODO: 可能需要给个工厂
class BaseRuntimeWithModelConfig (TypedDict):
    base_url: str
    model_name: str
    api_key:str # TODO: 这个要怎么做脱敏呢?
    provider: str = "openai"
    top_k: float|None = None
    temperature: float|None = None


    