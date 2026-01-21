from typing import List, Optional, Any, Dict, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AnnotationCreateDTO(BaseModel):
    type: str
    rects: List[Dict[str, Any]]
    content: Optional[str] = None
    color: Optional[str] = None


class AnnotationUpdateDTO(BaseModel):
    content: Optional[str] = None
    color: Optional[str] = None


class AnnotationDTO(BaseModel):
    id: UUID
    layer_id: UUID
    type: str
    rects: List[Dict[str, Any]]
    content: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LayerCreateDTO(BaseModel):
    name: str
    type: str = "user"
    visible: bool = True


class LayerUpdateDTO(BaseModel):
    name: Optional[str] = None
    visible: Optional[bool] = None


class LayerDTO(BaseModel):
    id: UUID
    paper_id: UUID
    user_id: UUID
    name: str
    type: str = "user"
    visible: bool = True
    created_at: datetime
    annotations: List[AnnotationDTO] = []

    model_config = ConfigDict(from_attributes=True)


class LayerListDTO(BaseModel):
    layers: List[LayerDTO]


class SummaryCreateDTO(BaseModel):
    summary_type: str = "abstract_rewrite"


class SummaryDTO(BaseModel):
    id: UUID
    paper_id: UUID
    summary_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreateDTO(BaseModel):
    title: Optional[str] = None
    content: str


class NoteUpdateDTO(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteDTO(BaseModel):
    id: UUID
    paper_id: UUID
    user_id: UUID
    title: Optional[str] = None
    page: Optional[int] = None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNodeDTO(BaseModel):
    id: str
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class GraphEdgeDTO(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class GraphDataDTO(BaseModel):
    nodes: List[GraphNodeDTO]
    edges: List[GraphEdgeDTO]


class MindMapCreateDTO(BaseModel):
    graph_data: Optional[GraphDataDTO] = None


class MindMapUpdateDTO(BaseModel):
    graph_data: GraphDataDTO


class MindMapDTO(BaseModel):
    id: UUID
    paper_id: UUID
    graph_data: GraphDataDTO
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AISummary(BaseModel):
    summary_config: Dict[str, str] = Field(..., description="论文AI总结, 键为总结的类型(和设置项相关), 值为目录项对应的总结")


# --- Moved from Controller Schema ---

class TocItem(BaseModel):
    title: str = Field(..., description="目录项标题")
    page: int = Field(..., description="目录项对应的页码")


class Toc(BaseModel):
    items: List[TocItem] = Field(..., description="目录项")


class Rect(BaseModel):
    x: float = Field(..., description="矩形左上角的 x 坐标")
    y: float = Field(..., description="矩形左上角的 y 坐标")
    width: float = Field(..., description="矩形的宽度")
    height: float = Field(..., description="矩形的高度")
    page_index: int = Field(..., alias="pageIndex", description="矩形所在的页码索引 (从 0 开始)")
    model_config = ConfigDict(populate_by_name=True)


class Annotation(BaseModel):
    annotation_id: UUID = Field(..., alias="id", description="标注ID")
    type: Literal['highlight', 'translation', 'note'] = Field(..., description="标注类型(highlight/note/translate)")
    rect: List[Rect] = Field(..., description="标注区域坐标(JSON数组)")
    content: Optional[str] = Field(None, description="标注内容(笔记/翻译结果)")
    color: Optional[str] = Field(None, description="标注颜色(Hex/RGB)")

    model_config = ConfigDict(populate_by_name=True)


class View(BaseModel):
    view_id: UUID = Field(..., alias="id", description="图层ID")
    name: str = Field(..., description="图层名称")
    enable: bool = Field(..., alias="visible", description="是否可见")
    annotations: List[Annotation] = Field(..., description="视图注解")

    model_config = ConfigDict(populate_by_name=True)


class NoteMeta(BaseModel):
    note_id: UUID = Field(..., alias="id", description="笔记id")
    title: Optional[str] = Field(None, description="笔记标题")
    page: Optional[int] = Field(None, description="笔记对应的页码,默认为空")
    created_at: datetime = Field(..., description="创建的时间")

    model_config = ConfigDict(populate_by_name=True)


class MindMapNode(BaseModel):
    id: str = Field(..., description="节点id")
    text: str = Field(..., alias="label", description="节点文本")
    type: Optional[str] = Field(None, description="节点类型(可选)")
    meta: Optional[Dict[str, str]] = Field(None, description="节点元数据(可选)")
    
    model_config = ConfigDict(populate_by_name=True)


class MindMapEdge(BaseModel):
    from_id: str = Field(..., alias="source", description="边的起始节点id")
    to_id: str = Field(..., alias="target", description="边的结束节点id")
    label: Optional[str] = Field(None, description="边的标签(可选)")

    model_config = ConfigDict(populate_by_name=True)


class MindMap(BaseModel):
    nodes: List[MindMapNode] = Field(..., description="节点列表")
    edges: List[MindMapEdge] = Field(..., description="边列表")


class Record(BaseModel):
    record_id: UUID = Field(..., alias="id", description="记录id")
    title: Optional[str] = Field(..., description="对话记录的标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(populate_by_name=True)


class Message(BaseModel):
    message_id: UUID = Field(..., description="消息id")
    type: Literal['HUMAN', 'AI', 'TOOL_CALL', 'TOOL_RESPONSE'] = Field(..., description="消息类型")
    content: str = Field(..., alias="context", description="消息内容")
    created_at: datetime = Field(..., description="发送时间")

    model_config = ConfigDict(populate_by_name=True)


class JobResult(BaseModel):
    toc: Optional[Toc] = None
    summary: Optional[AISummary] = None
    mind_map: Optional[MindMap] = None
    chat: Optional[List[Message]] = None
    deep_research: Optional[List[Message]] = None


class Job(BaseModel):
    job_id: UUID = Field(..., alias="id", description="作业ID")
    type: Literal['toc', 'summary', 'mind_map', 'deep_research', 'chat'] = Field(..., alias="job_type", description="作业类型")
    status: Literal['queued', 'running', 'blocked', 'succeeded', 'failed', 'canceled', 'expired'] = Field(..., description="作业状态")
    progress: Optional[float] = Field(None, description="作业进度(0-1)")
    stage: Optional[str] = Field(None, description="作业当前阶段")
    result: Optional[JobResult] = Field(None, description="结果引用")
    error: Optional[str] = Field(None, alias="error_message", description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    end_at: Optional[datetime] = Field(None, alias="completed_at", description="完成时间")

    model_config = ConfigDict(populate_by_name=True)


class PaperReaderMeta(BaseModel):
    paper_id: UUID
    file_url: Optional[str] = None
    summary: Optional[AISummary] = None
    toc: Optional[Toc] = None
    views: List[View]
    notes: List[NoteMeta]
    mind_map: Optional[MindMap] = None
    history: List[Record]
    jobs: List[Job]
