# 定义pg数据库的实体映射。 

'''
开发者: BackendAgent
当前版本: v1.3_db_models
创建时间: 2026年01月08日 11:00
更新时间: 2026年01月12日 08:00
更新记录:
    [2026年01月08日 11:00:v1.0_db_models:创建数据库模型文件，包含所有核心表结构]
    [2026年01月08日 16:30:v1.1_db_models:从/src/business_model/database_models.py迁移到/src/base/pg/entity.py中]
    [2026年01月12日 07:50:v1.2_db_models:为所有实体类添加详细文档注释(Docstring)]
    [2026年01月12日 08:00:v1.3_db_models:为数据库表和字段添加物理注释(Comment)，支持数据库级元数据查看]
'''

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel

from common.model.enums import PaperStatus
from service.setting.schema import Settings
from common.db_types import PydanticJSON


class User(SQLModel, table=True):
    """
    用户表模型 (User Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00
    
    用途:
        存储系统用户的基本信息、认证凭据及状态。
    
    字段:
        id: 用户全局唯一标识 (UUID)。
        email: 用户邮箱 (登录账号)，唯一索引。
        hashed_password: 加密后的密码哈希值，而非明文。
        full_name: 用户全名/昵称 (可选)。
        is_active: 账号是否激活 (True:激活, False:禁用/删除)。
        created_at: 账号创建时间。
        updated_at: 账号最后更新时间。
    
    使用场景:
        - 用户注册、登录认证 (Auth Service)。
        - 关联用户上传的论文、聊天记录、阅读标注等资源。
        - 权限控制与用户信息查询。
    
    内部实现:
        - 继承自 SQLModel，对应数据库表 'users'。
        - id: 使用 UUID 作为主键，确保全局唯一性。
        - email: 唯一索引，用于登录标识。
        - hashed_password: 存储加密后的密码哈希值，而非明文。
        - is_active: 软删除标记，用于禁用用户而非直接删除数据。
        - 关联: 
            - papers: 一对多关联 Paper 表。
            - agent_sessions: 一对多关联 AgentSession 表。
    """
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表: 存储系统用户的基本信息、认证凭据及状态"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户全局唯一标识(UUID)"}
    )
    email: str = Field(
        unique=True, 
        index=True,
        sa_column_kwargs={"comment": "用户邮箱(登录账号)"}
    )
    hashed_password: str = Field(
        sa_column_kwargs={"comment": "加密后的密码哈希值"}
    )
    full_name: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "用户全名/昵称"}
    )
    is_active: bool = Field(
        default=True,
        sa_column_kwargs={"comment": "账号是否激活(True:激活, False:禁用/删除)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "账号创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "账号最后更新时间"}
    )
    
    settings: Settings = Field(
        default_factory=Settings,
        sa_type=PydanticJSON(Settings),
        sa_column_kwargs={"comment": "用户个性化设置"}
    )

    # 关联关系
    papers: List["Paper"] = Relationship(back_populates="user")
    agent_sessions: List["AgentSession"] = Relationship(back_populates="user")
    collections: List["Collection"] = Relationship(back_populates="user")
    notes: List["Note"] = Relationship(back_populates="user")
    mind_maps: List["MindMap"] = Relationship(back_populates="user")

class Paper(SQLModel, table=True):
    """
    论文表模型 (Paper Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储用户上传或导入的论文元数据及处理状态。

    使用场景:
        - 论文列表展示与详情查询。
        - 论文上传、解析状态跟踪 (Pending -> Processing -> Completed)。
        - 关联论文的向量切片 (Chunks)、摘要 (Summaries) 和阅读标注 (Layers/Annotations)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'papers'。
        - user_id: 外键关联 Users 表，标识论文归属。
        - authors: 使用 JSON 类型存储作者列表，灵活适应不同数量的作者。
        - file_key: 存储对象存储 (如 MinIO) 中的文件路径或 Key。
        - status: 枚举类型 (PaperStatus)，管理论文处理生命周期。
        - 关联:
            - chunks: 一对多关联 PaperChunk，用于RAG检索。
            - layers: 一对多关联 Layer，用于阅读器标注。
            - reports: 一对多关联 Report，用于生成的研究报告。
    """
    __tablename__ = "papers"
    __table_args__ = {"comment": "论文表: 存储论文元数据、文件路径及处理状态"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "论文全局唯一标识(UUID)"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )

    # 基本信息
    title: str = Field(
        index=True,
        sa_column_kwargs={"comment": "论文标题"}
    )
    authors: List[str] = Field(
        sa_column=Column(JSON, comment="作者列表(JSON数组)")
    )
    abstract: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "论文摘要原文"}
    )
    toc: Optional[List] = Field(
        default=None,
        sa_column=Column(JSON, comment="论文目录结构(TOC)")
    )

    # 文件存储

    file_key: str = Field(
        sa_column_kwargs={"comment": "文件存储Key/路径(MinIO或本地)"}
    )
    file_url: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "文件访问URL(可选),若为本地的则为nginx代理的相对位置。给前端用的"}
    )
    source_type: Optional[str] =  Field(
        default=None,
        sa_column_kwargs={"comment": "文件来源类型(如arXiv、PDF等)"}
    )
    source_ref: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "文件来源引用(如arXiv ID、PDF URL等)"}
    )

    # 状态管理
    status: PaperStatus = Field(
        default=PaperStatus.PENDING,
        sa_column_kwargs={"comment": "处理状态(PENDING/PROCESSING/COMPLETED/FAILED)"}
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "处理失败时的错误信息"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "上传/创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    # 关联关系
    user: User = Relationship(back_populates="papers")
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
    summaries: List["PaperSummary"] = Relationship(back_populates="paper")
    layers: List["Layer"] = Relationship(back_populates="paper")
    reports: List["Report"] = Relationship(back_populates="paper")
    chat_sessions: List["AgentSession"] = Relationship(back_populates="paper")
    notes: List["Note"] = Relationship(back_populates="paper")
    mind_map: Optional["MindMap"] = Relationship(back_populates="paper")

class PaperChunk(SQLModel, table=True):
    """
    论文向量切片表模型 (Paper Chunk Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储论文经解析、拆分后的文本片段及其向量表示 (Embedding)，用于 RAG (检索增强生成)。

    使用场景:
        - 向量检索: 根据用户 Query 查找相关论文片段。
        - 问答系统: 为 LLM 提供上下文依据。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'paper_chunks'。
        - paper_id: 外键关联 Papers 表。
        - content: 存储切片后的纯文本内容。
        - chunk_index: 记录切片在原文档中的顺序，用于上下文重组。
        - embedding: 使用 pgvector 扩展存储高维向量 (1536维，适配 OpenAI text-embedding-3-small 或兼容模型)。
            - 注意: 需要数据库开启 vector 扩展。
    """
    __tablename__ = "paper_chunks"
    __table_args__ = {"comment": "论文切片表: 存储解析后的文本片段及向量Embedding"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "切片唯一标识"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    # 内容信息
    content: str = Field(
        sa_column_kwargs={"comment": "切片文本内容"}
    )
    page_number: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"comment": "所在页码"}
    )
    chunk_index: int = Field(
        sa_column_kwargs={"comment": "切片顺序索引"}
    )

    embedding: List[float] = Field(
        sa_column=Column(Vector(1536), comment="向量Embedding(默认1536维)")
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        sa_column_kwargs={"comment": "用于生成Embedding的模型"}
    )
    embedding_dim: int = Field(
        default=1536,
        sa_column_kwargs={"comment": "Embedding向量维度"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="chunks")

class Collection(SQLModel, table=True):
    """
    收藏夹表模型 (Collection Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 15:00:00

    用途:
        存储用户创建的论文收藏夹/合集。

    使用场景:
        - 用户创建自定义分类收藏夹。
        - 将论文添加到收藏夹以便管理。
    """
    __tablename__ = "collections"
    __table_args__ = {"comment": "收藏夹表: 用户自定义的论文集合"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "收藏夹ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    name: str = Field(
        index=True,
        sa_column_kwargs={"comment": "收藏夹名称"}
    )
    is_default: bool = Field(
        default=False,
        index=True,
        sa_column_kwargs={"comment": "是否为默认收藏夹"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="collections")
    # 通过中间表关联论文
    # papers: List["Paper"] = Relationship(link_model=CollectionPaper) # 暂不直接定义反向，按需查询

class CollectionPaper(SQLModel, table=True):
    """
    收藏夹-论文关联表 (Collection Paper Association)
    
    注释者: BackendAgent
    注释时间: 2026-01-12 15:00:00
    
    用途:
        实现收藏夹与论文的多对多关联。
    """
    __tablename__ = "collection_papers"
    __table_args__ = {"comment": "收藏夹-论文关联表"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联ID"}
    )
    collection_id: UUID = Field(
        foreign_key="collections.id",
        primary_key=False,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "收藏夹ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        primary_key=False,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "论文ID"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "收藏时间"}
    )

class SearchHistory(SQLModel, table=True):
    """
    搜索历史表模型 (Search History Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 18:00:00

    用途:
        记录用户的搜索历史，用于提供搜索建议、历史回溯和用户兴趣分析。

    使用场景:
        - 用户在搜索框输入时显示最近搜索记录。
        - 分析用户感兴趣的领域。
    """
    __tablename__ = "search_histories"
    __table_args__ = {"comment": "搜索历史表: 记录用户的搜索关键词及上下文"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "记录ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    
    user: Optional["User"] = Relationship()

    session_name: str = Field(
        index=True,
        sa_column_kwargs={"comment": "搜索关键词"}
    )
    filters: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, comment="搜索过滤条件(JSON)")
    )
    result_count: int = Field(
        default=0,
        sa_column_kwargs={"comment": "搜索结果数量"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "搜索时间"}
    )

    # 关联关系 (可选)
    # user: User = Relationship(back_populates="search_histories") 
    # 暂不在 User 中定义反向关系以避免 User 类过于臃肿

class PaperSummary(SQLModel, table=True):
    """
    论文摘要表模型 (Paper Summary Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储论文的多维度摘要信息。

    使用场景:
        - 快速预览: 用户在阅读正文前查看简要总结。
        - 结构化提取: 存储如 "创新点", "方法论", "实验结果" 等特定类型的摘要。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'paper_summaries'。
        - summary_type: 区分摘要类型 (如 'abstract_rewrite', 'key_points', 'methodology')。
        - content: 摘要文本内容。
    """
    __tablename__ = "paper_summaries"
    __table_args__ = {"comment": "论文摘要表: 存储多维度的论文总结与分析"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "摘要ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    # 摘要内容
    summary_type: str = Field(
        sa_column_kwargs={"comment": "摘要类型(如short, detailed, key_points)"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "摘要内容"}
    )
    version: int = Field(default=1, sa_column_kwargs={"comment": "摘要版本号"})
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "生成时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    # 关联关系
    paper: Paper = Relationship(back_populates="summaries")

class Report(SQLModel, table=True):
    """
    研究报告表模型 (Report Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储 Agent 生成的深度研究报告。

    使用场景:
        - 深度调研 (Deep Research): 基于单篇或多篇论文生成的综合分析报告。
        - 相关工作 (Related Work): 自动生成的文献综述。
        - 报告查看与导出 (Markdown 格式)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'reports'。
        - paper_id: 外键关联 Papers 表 (目前设计为关联单篇，未来可能需要关联多篇或通过 Tags 关联)。
        - type: 报告类型 ('deep_research', 'related_work')。
        - status: 生成状态流转 ('generating' -> 'completed' / 'failed')，用于前端轮询或 SSE 通知。
        - content: 存储 Markdown 格式的报告正文。
    """
    __tablename__ = "reports"
    __table_args__ = {"comment": "研究报告表: 存储Agent生成的分析报告"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "报告ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "基于的论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )

    title: str = Field(
        sa_column_kwargs={"comment": "报告标题"}
    )
    type: str = Field(
        sa_column_kwargs={"comment": "报告类型(deep_research/related_work)"}
    )
    status: str = Field(
        default="generating",
        sa_column_kwargs={"comment": "生成状态(generating/completed/failed)"}
    )
    content: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "报告正文(Markdown)"}
    )
    summary: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "报告摘要"}
    )
    job_id: Optional[UUID] = Field(
        default=None,
        foreign_key="jobs.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联任务ID(可选)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="reports")

class Note(SQLModel, table=True):
    """
    笔记表模型 (Note Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储用户对论文的个人注释、摘要、标签等。

    使用场景:
        - 记录对论文的关键理解、问题、建议等。
        - 组织和分类用户的研究笔记。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'notes'。
        - paper_id: 外键关联 Papers 表。
        - content: 存储用户的 Markdown 格式笔记内容。
        - tags: JSON 字段，存储用户添加的标签 (如 'important', 'question')。
    """
    __tablename__ = "notes"
    __table_args__ = {"comment": "笔记表: 存储用户对论文的个人注释"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "笔记ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    title: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "笔记标题"}
    )
    page: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"comment": "笔记对应的页码"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "笔记内容(Markdown)"}
    )
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, comment="标签(JSON数组)")
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,   
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="notes")
    user: User = Relationship(back_populates="notes")

class MindMap(SQLModel, table=True):
    """
    思维导图/知识图谱表模型 (Mind Map Model)
    
    注释者: BackendAgent
    注释时间: 2026-01-14 16:45:00
    
    用途:
        存储论文的知识结构图 (节点与边)。
        
    使用场景:
        - 侧边栏 "脑图" Tab，展示论文核心概念及其关系。
        - 支持前端 reagraph 渲染。
        - 存储 Agent 生成的图谱数据或用户手动编辑的结果。
    """
    __tablename__ = "mind_maps"
    __table_args__ = {"comment": "思维导图表: 存储论文的知识结构(节点与边)"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "脑图ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    
    # 存储图数据: { "nodes": [...], "edges": [...] }
    # 节点结构: { "id": "...", "label": "...", "data": {...} }
    # 边结构: { "id": "...", "source": "...", "target": "...", "label": "..." }
    # TODO: 考虑是否对象映射。也准备改为对象映射吧。
    graph_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, comment="图数据(JSON):包含nodes和edges")
    )
    schema_version: int = Field(
        default=1,
        sa_column_kwargs={"comment": "图数据 schema 版本"}
    )
    status: str = Field(
        default="ready",
        sa_column_kwargs={"comment": "状态(ready/archived)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联
    paper: Paper = Relationship(back_populates="mind_map")
    user: User = Relationship(back_populates="mind_maps")


class Layer(SQLModel, table=True):
    """
    阅读器图层表模型 (Reader Layer Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        支持 PDF 阅读器的多图层标注功能，类似 Photoshop 图层概念。

    使用场景:
        - 多人协作: 区分 "我的标注"、"团队标注"、"AI 自动标注"。
        - 标注分类: 区分 "高亮层"、"翻译层"、"笔记层"。
        - 控制标注的可见性 (visible 字段)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'layers'。
        - paper_id: 外键关联 Papers 表。
        - type: 图层类型 ('user' 为用户创建, 'system' 为系统生成)。
        - 关联:
            - annotations: 一对多关联 Annotation，该图层下的所有具体标注。
    """
    __tablename__ = "layers"
    __table_args__ = {"comment": "阅读器图层表: 支持多层级标注管理"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "图层ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "创建者用户ID"}
    )

    name: str = Field(
        sa_column_kwargs={"comment": "图层名称"}
    )
    type: str = Field(
        default="user",
        sa_column_kwargs={"comment": "图层类型(user/system)"}
    )
    visible: bool = Field(
        default=True,
        sa_column_kwargs={"comment": "是否可见"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now, 
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )




    # 关联关系
    paper: Paper = Relationship(back_populates="layers")
    annotations: List["Annotation"] = Relationship(back_populates="layer")


class Annotation(SQLModel, table=True):
    """
    标注表模型 (Annotation Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储 PDF 阅读器中的具体标注对象。

    使用场景:
        - 高亮 (Highlight): 标记重要文本。
        - 笔记 (Note/Comment): 对特定区域添加文字批注。
        - 划词翻译 (Translate): 保存翻译记录。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'annotations'。
        - layer_id: 外键关联 Layers 表，必须依附于某个图层。
        - rects: JSON 字段，存储标注在 PDF 页面上的几何坐标 (x, y, width, height, pageIndex)，前端利用此信息渲染。
        - content: 存储笔记内容或翻译结果文本。
        - color: 标注颜色，支持个性化配置。
    """
    __tablename__ = "annotations"
    __table_args__ = {"comment": "标注表: 存储PDF的高亮、笔记等标注信息"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "标注ID"}
    )
    layer_id: UUID = Field(
        foreign_key="layers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属图层ID"}
    )

    type: str = Field(
        sa_column_kwargs={"comment": "标注类型(highlight/note/translate)"}
    )
    # 存储矩形坐标 [{"x":.., "y":.., "width":.., "height":.., "pageIndex":..}]
    rects: List[dict] = Field(
        sa_column=Column(JSON, comment="标注区域坐标(JSON数组)")
    )
    content: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "标注内容(笔记/翻译结果)"}
    )
    color: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "标注颜色(Hex/RGB)"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    
    # 关联关系
    layer: Layer = Relationship(back_populates="annotations")


class AgentSession(SQLModel, table=True):
    """
    Agent 会话表
    存储 Agent 的运行实例信息，关联到用户的聊天会话
    """
    __tablename__ = "agent_sessions"
    __table_args__ = {"comment": "Agent会话表: 存储Agent运行实例信息"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "会话ID"}
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    user: Optional["User"] = Relationship(back_populates="agent_sessions")

    paper_id: Optional[UUID] = Field(
        default=None,
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联论文ID(可选)"}
    )

    title: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "会话标题"}
    )

    thread_id: str = Field(
        sa_column=Column(Text, unique=True, index=True, comment="LangGraph线程ID")
    )

    agent_type: str = Field(
        sa_column_kwargs={"comment": "Agent类型(search/paper_chat/summary/mindmap/deep_research)"}
    )

    status: str = Field(
        default="active",
        sa_column_kwargs={"comment": "会话状态(active/interrupted/completed/error)"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now    ,
        sa_column_kwargs={"comment": "创建时间"}
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    paper: Optional["Paper"] = Relationship(back_populates="chat_sessions")


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    __table_args__ = {"comment": "作业表: 存储异步任务信息"}
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "作业ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    paper_id: Optional[UUID] = Field(
        default=None,
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联的论文ID"}
    )
    job_type: str = Field(
        sa_column_kwargs={"comment": "作业类型(search/paper_chat/summary/mindmap/deep_research)"}
    )
    status: str = Field(
        default="pending",
        sa_column_kwargs={"comment": "作业状态(queued/running/blocked/succeeded/failed/canceled/expired)"}
    )
    progress: int = Field(
        default=0,
        sa_column_kwargs={"comment": "作业进度(0-100)"}
    )
    stage: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "作业当前阶段"}
    )
    idempotency_key: str = Field(
        index=True,
        sa_column_kwargs={"comment": "幂等键"}
    )
    dependency_ids: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, comment="依赖作业ID列表(JSON数组)")
    )
    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, comment="作业负载(JSON对象)")
    )
    result_ref: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "结果引用"}
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "错误信息"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "完成时间"}
    )
