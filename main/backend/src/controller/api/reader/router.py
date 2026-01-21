from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends, Body
from controller.response import Response
from service.reader.reader_service import ReaderServiceDep
from service.reader.toc_service import TocService
from service.reader.view_service import ViewService
from service.reader.note_service import NoteService
from service.reader.summary_service import SummaryService
from service.reader.mind_map_service import MindMapService
from service.reader.history_service import HistoryService
from service.reader.job_service import JobService
from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from base.pg.entity import User
from controller.api.reader.schema import (
    PaperReaderMetaResponse, TocResponse, ViewResponse,
    NoteMetaResponse, NoteResponse, AISummaryResponse,
    MindMapResponse, RecordResponse, MessageResponse, JobListResponse,
    AnnotationResponse, AnnotationRequest, JobResponse, JobCreateRequest
)

router = APIRouter(prefix="/papers", tags=["reader"])

# Service Dependencies
def get_toc_service(session: SessionDep) -> TocService:
    return TocService(session)

def get_view_service(session: SessionDep) -> ViewService:
    return ViewService(session)

def get_note_service(session: SessionDep) -> NoteService:
    return NoteService(session)

def get_summary_service(session: SessionDep) -> SummaryService:
    return SummaryService(session)

def get_mind_map_service(session: SessionDep) -> MindMapService:
    return MindMapService(session)

def get_history_service(session: SessionDep) -> HistoryService:
    return HistoryService(session)

def get_job_service(session: SessionDep) -> JobService:
    return JobService(session)

TocServiceDep = Annotated[TocService, Depends(get_toc_service)]
ViewServiceDep = Annotated[ViewService, Depends(get_view_service)]
NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]
SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
MindMapServiceDep = Annotated[MindMapService, Depends(get_mind_map_service)]
HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]


@router.get("/{paper_id}/meta", response_model=Response[PaperReaderMetaResponse])
async def get_paper_meta(
    paper_id: UUID, 
    service: ReaderServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文元数据"""
    data = await service.get_paper_meta(paper_id, current_user.id)
    return Response.success(PaperReaderMetaResponse.model_validate(data.model_dump()))

@router.get("/{paper_id}/toc", response_model=Response[TocResponse])
async def get_toc(
    paper_id: UUID, 
    service: TocServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文目录"""
    data = await service.get_toc(paper_id, current_user.id)
    return Response.success(TocResponse(items=data.items))

@router.get("/{paper_id}/views", response_model=Response[List[ViewResponse]])
async def get_views(
    paper_id: UUID, 
    service: ViewServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文视图"""
    data = await service.get_views(paper_id, current_user.id)
    return Response.success(data)

@router.get("/{paper_id}/notes", response_model=Response[NoteMetaResponse])
async def get_notes(
    paper_id: UUID, 
    service: NoteServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文笔记列表"""
    data = await service.get_notes_meta(paper_id, current_user.id)
    return Response.success(NoteMetaResponse(items=data))

@router.get("/{paper_id}/notes/{note_id}", response_model=Response[NoteResponse])
async def get_note_detail(
    paper_id: UUID, 
    note_id: UUID, 
    service: NoteServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取笔记详情"""
    data = await service.get_note_detail(paper_id, note_id, current_user.id)
    return Response.success(NoteResponse.model_validate(data.model_dump()))

@router.get("/{paper_id}/ai/summary", response_model=Response[AISummaryResponse])
async def get_ai_summary(
    paper_id: UUID, 
    service: SummaryServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文AI总结"""
    data = await service.get_ai_summary(paper_id, current_user.id)
    if data:
        return Response.success(AISummaryResponse(summary_config=data.summary_config))
    return Response.success(AISummaryResponse(summary_config={}))

@router.get("/{paper_id}/ai/mind_map", response_model=Response[MindMapResponse])
async def get_mind_map(
    paper_id: UUID, 
    service: MindMapServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文AI脑图"""
    data = await service.get_mind_map_data(paper_id, current_user.id)
    return Response.success(MindMapResponse(nodes=data.nodes, edges=data.edges))

@router.get("/{paper_id}/ai/history", response_model=Response[List[RecordResponse]])
async def get_ai_history(
    paper_id: UUID, 
    service: HistoryServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文AI历史"""
    data = await service.get_ai_history(paper_id, current_user.id)
    return Response.success(data)

@router.get("/{paper_id}/ai/record/{record_id}", response_model=Response[MessageResponse])
async def get_record_detail(
    paper_id: UUID, 
    record_id: UUID, 
    service: HistoryServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取AI阅读记录详情"""
    data = await service.get_record_detail(paper_id, record_id, current_user.id)
    return Response.success(MessageResponse(items=data))

@router.get("/{paper_id}/jobs", response_model=Response[JobListResponse])
async def get_jobs(
    paper_id: UUID, 
    service: JobServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取当前论文处理任务"""
    data = await service.get_jobs(paper_id, current_user.id)
    return Response.success(JobListResponse(items=data))


@router.post("/{paper_id}/jobs", response_model=Response[JobResponse])
async def create_job(
    paper_id: UUID,
    req: JobCreateRequest,
    service: JobServiceDep,
    current_user: User = Depends(get_current_user)
):
    """创建任务"""
    data = await service.create_job(paper_id, req, current_user.id)
    return Response.success(data)


@router.post("/{paper_id}/views", response_model=Response[ViewResponse])
async def create_view(
    paper_id: UUID,
    name: str = Body(..., embed=True),
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """创建视图"""
    data = await service.create_view(paper_id, name, current_user.id)
    return Response.success(data)


@router.patch("/{paper_id}/views/{view_id}/rename")
async def rename_view(
    paper_id: UUID,
    view_id: UUID,
    name: str = Body(..., embed=True),
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """重命名视图"""
    await service.rename_view(view_id, name, current_user.id)
    return Response.success()


@router.patch("/{paper_id}/views/{view_id}/enable")
async def enable_view(
    paper_id: UUID,
    view_id: UUID,
    enable: bool = Body(..., embed=True),
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """启用/关闭视图"""
    await service.enable_view(view_id, enable, current_user.id)
    return Response.success()


@router.delete("/{paper_id}/views/{view_id}")
async def delete_view(
    paper_id: UUID,
    view_id: UUID,
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """删除视图"""
    await service.delete_view(view_id, current_user.id)
    return Response.success()


@router.get("/{paper_id}/views/{view_id}/annotations", response_model=Response[AnnotationResponse])
async def get_annotations(
    paper_id: UUID,
    view_id: UUID,
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """获取视图注解"""
    data = await service.get_annotations(paper_id, view_id, current_user.id)
    return Response.success(data)


@router.post("/{paper_id}/views/{view_id}/annotations")
async def add_annotation(
    paper_id: UUID,
    view_id: UUID,
    req: AnnotationRequest,
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """对论文进行标注"""
    await service.add_annotation(paper_id, view_id, req, current_user.id)
    return Response.success()


@router.delete("/{paper_id}/views/{view_id}/annotations/{annotation_id}")
async def delete_annotation(
    paper_id: UUID,
    view_id: UUID,
    annotation_id: UUID,
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """删除标注"""
    await service.delete_annotation(paper_id, view_id, annotation_id, current_user.id)
    return Response.success()


@router.put("/{paper_id}/views/{view_id}/annotations/{annotation_id}")
async def update_annotation(
    paper_id: UUID,
    view_id: UUID,
    annotation_id: UUID,
    req: AnnotationRequest,
    service: ViewServiceDep = None,
    current_user: User = Depends(get_current_user)
):
    """修改标注"""
    await service.update_annotation(paper_id, view_id, annotation_id, req, current_user.id)
    return Response.success()
