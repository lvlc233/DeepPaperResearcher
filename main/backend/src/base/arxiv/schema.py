from typing import List, Optional
from pydantic import BaseModel

class ArxivPaperInfo(BaseModel):
    '''
    arXiv论文信息模型 (Infrastructure Output)
    
    描述:
    用于表示从arXiv XML解析得到的原始论文数据。
    这是Arxiv模块的输出契约。
    '''
    title: str
    authors: List[str]
    abstract: str
    paper_url: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    categories: List[str] = []
    source_id: Optional[str] = None
