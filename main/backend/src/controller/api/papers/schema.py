'''
开发者: BackendAgent
当前版本: v0.3_papers_status_optional
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月09日 10:19
更新记录:
    [2026年01月09日 10:19:v0.3_papers_status_optional:PaperStatusResponse的updated_at改为可选，适配当前实体模型]
    [2026年01月08日 17:30:v0.2_papers_upload:添加论文上传相关请求模型]
    [2026年01月02日 10:16:v0.1_papers:重新定义PaperFetchRequest，符合Controller层职责]
    [2026年01月02日 08:54:v0.1_paper_requests:直接导入business_model，不符合规范]
'''

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PaperFetchRequest(BaseModel):
    '''
    论文集获取请求模型（Controller层）

    字段说明:
    - url: 论文集页面URL（如arXiv列表页或搜索结果页）
    - source: 论文来源（如'arXiv'），用于指定使用哪个数据源解析器

    使用场景:
    - Controller层接收前端传入的请求
    - FastAPI使用此模型自动验证请求参数
    - 验证通过后传递给Service层处理

    约束:
    - url为必填项，不能为空
    - source默认为"arXiv"，支持多学术网站

    注意:
    - 此模型专门用于Controller层接收请求
    - 不应该在business_model中定义请求模型
    '''
    url: str
    source: str = "arXiv"  # 默认为arXiv，后续可扩展其他来源如IEEE, ACM等


class PaperUploadRequest(BaseModel):
    '''
    论文上传请求模型（Controller层）

    字段说明:
    - title: 论文标题（可选，如果未提供则从PDF元数据提取）
    - authors: 作者列表（可选，如果未提供则从PDF元数据提取）

    使用场景:
    - Controller层接收前端上传的PDF文件
    - 与UploadFile一起使用，支持multipart/form-data
    - 验证通过后传递给PaperService处理

    注意:
    - 此模型用于接收表单字段
    - PDF文件通过UploadFile单独接收
    '''
    title: Optional[str] = None
    authors: Optional[str] = None  # JSON字符串格式


class PapersUploadWebRequest(BaseModel):
    """网络论文上传请求"""
    urls: List[str] = Field(..., description="论文的url列表,需要指向pdf")
    collection_id: Optional[UUID] = Field(None, description="默认指向默认收藏夹")


class PapersUploadResponse(BaseModel):
    """论文上传响应"""
    paper_id: UUID = Field(..., description="论文全局唯一标识")
    title: str = Field(..., description="论文标题")
    status: str = Field(..., description="处理状态")  # Literal['processing','success','failed']
    message: Optional[str] = None


class PaperStatusResponse(BaseModel):
    '''
    论文状态响应模型
    字段说明:
    - paper_id: 论文唯一ID
    - status: 处理状态（pending/processing/completed/failed）
    - title: 论文标题
    - authors: 作者列表
    - abstract: 论文摘要
    - progress: 处理进度百分比（0-100）
    - error_message: 错误信息（如果处理失败）
    - created_at: 创建时间
    - updated_at: 更新时间
    '''
    paper_id: str = Field(..., description="论文唯一ID")
    status: str = Field(..., description="处理状态（pending/processing/completed/failed）")
    title: Optional[str] = Field(None, description="论文标题")
    authors: Optional[List[str]] = Field(None, description="作者列表")
    abstract: Optional[str] = Field(None, description="论文摘要")
    progress: int = Field(default=0, ge=0, le=100, description="处理进度百分比")
    error_message: Optional[str] = Field(None, description="错误信息（如果处理失败）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    toc: Optional[List] = Field(None, description="目录结构 (Table of Contents)，通常包含章节标题、层级和页码")
    file_url: Optional[str] = Field(None, description="文件访问URL")


__all__ = ["PaperFetchRequest", "PaperUploadRequest", "PaperStatusResponse"]
