'''
开发者: BackendAgent
当前版本: v0.4_papers_absolute_file_url
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月17日 23:24
更新记录:
    [2026年01月17日 21:58:v0.3_papers_x_accel_redirect:论文文件下载改为X-Accel-Redirect，交由Nginx托管文件流]
    [2026年01月17日 23:24:v0.4_papers_absolute_file_url:状态/详情接口返回绝对 file_url，避免前端以自身域名请求导致404]
    [2026年01月09日 10:19:v0.2_papers_upload_status:补齐论文上传、状态查询、触发处理与列表接口，避免与动态路由冲突]
    [2026年01月02日 10:16:v0.1_papers:修复依赖注入和安全问题，使用Depends注入服务]
    [2026年01月02日 08:54:v0.1_paper_router:全局实例化服务，违反依赖注入原则]
'''

import asyncio
import os
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Header, Form, Request
from fastapi.responses import Response as FastAPIResponse, FileResponse

from controller.api.papers.schema import (
    PaperFetchRequest,
    PaperStatusResponse,
    PapersUploadWebRequest,
    PapersUploadResponse,
)
from controller.api.collections.schema import (
    CollectionResponse,
)
from controller.api.auth.router import get_current_user
from controller.response import Response
from service.papers.schema import PaperListResponse, PaperInfo, PaperUploadResponse
from service.papers.arxiv_service import ArxivService
from service.papers.paper_service import PaperService, PaperProcessingService, PaperServiceDep
from service.collections.collection_service import CollectionServiceDep
from base.arxiv.client import ArxivClient
from base.arxiv.parser import ArxivXmlParser
from base.pg.entity import User
from common.model.enums import PaperStatus

# 配置日志
from loguru import logger

# 创建路由
router = APIRouter(prefix="/papers", tags=["papers"])

INTERNAL_UPLOADS_LOCATION_PREFIX = "/internal-uploads/"


def _resolve_file_url(request: Request, file_url: str) -> str:
    if not file_url:
        return file_url

    # 如果是网络的,就返回网络的
    normalized = file_url.strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    # 如果是本地的,就处理下
    # TODO: 感觉这个论文的本地化存储位置可以设置为配置项啊。
    if normalized.startswith("/"):
        return f"{str(request.base_url).rstrip('/')}{normalized}"

    return normalized


def get_arxiv_service() -> ArxivService:
    '''
    服务工厂函数

    创建ArxivService实例，并注入Infrastructure依赖

    返回:
    - ArxivService实例

    依赖注入:
    - 创建ArxivClient（Infrastructure层：处理HTTP通信）
    - 创建ArxivXmlParser（Infrastructure层：处理XML解析）
    - 将依赖注入ArxivService
    '''
    client = ArxivClient()
    parser = ArxivXmlParser()
    return ArxivService(client=client, parser=parser)


def get_paper_processing_service() -> PaperProcessingService:
    return PaperProcessingService()


def calculate_progress(status_value: PaperStatus) -> int:
    progress_map = {
        PaperStatus.PENDING: 10,
        PaperStatus.PROCESSING: 50,
        PaperStatus.COMPLETED: 100,
        PaperStatus.FAILED: 0,
    }
    return progress_map.get(status_value, 0)


def _log_background_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except Exception:
        logger.exception("论文处理后台任务失败")


@router.post("/fetch", response_model=Response[PaperListResponse])
async def fetch_papers(
    request: PaperFetchRequest,
    service: ArxivService = Depends(get_arxiv_service)
):
    '''
    从URL获取论文集

    接口说明:
    - 接收包含论文页面URL的请求
    - 从URL中提取并获取论文信息
    - 返回论文列表和元数据

    参数:
    - request: PaperFetchRequest对象，包含url和source字段
    - service: ArxivService实例（通过依赖注入获取）

    返回:
    - PaperListResponse对象，包含论文列表、总数、来源和原始URL

    错误处理:
    - 400: 请求参数无效
    - 422: URL格式不支持或无法解析
    - 500: 服务器内部错误

    使用示例:
    ```json
    {
        "url": "https://arxiv.org/pdf/2101.12345",
        "source": "arXiv"
    }
    ```

    响应示例:
    ```json
    {
        "papers": [
            {
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "abstract": "The dominant sequence transduction models...",
                "paper_url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                "published_date": "2017-06-12",
                "categories": ["cs.CL", "cs.LG"],
                "source_id": "1706.03762"
            }
        ],
        "total_count": 1,
        "source": "arXiv",
        "fetch_url": "https://arxiv.org/abs/2101.12345"
    }
    ```

    架构说明:
    - Controller层：接收请求，验证参数，返回响应（本函数）
    - Service层：处理业务逻辑（ArxivService）
    - Infrastructure层：处理HTTP和XML解析（ArxivClient, ArxivXmlParser）

    TODO:
    - 添加缓存机制（Redis）
    - 支持更多学术网站（IEEE, ACM, PubMed等）
    '''

    logger.info(f"接收到论文获取请求: url={request.url}, source={request.source}")

    try:
        # 验证输入
        if not request.url or not request.url.strip():
            logger.error("URL为空，返回400错误")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL不能为空"
            )

        # 根据source选择服务（目前仅支持arXiv，后续可扩展）
        if request.source.lower() != "arxiv":
            logger.error(f"不支持的数据源: {request.source}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"目前仅支持arXiv数据源，不支持: {request.source}"
            )

        # 调用Service层获取论文信息（依赖注入）
        logger.info("调用ArxivService获取论文信息")
        papers = await service.fetch_papers_from_url(request.url)

        # 构建响应
        total_count = len(papers)
        logger.info(f"成功获取 {total_count} 篇论文")

        response = PaperListResponse(
            papers=papers,
            total_count=total_count,
            source=request.source,
            fetch_url=request.url
        )

        logger.info("论文获取完成，返回响应")
        return Response.success(data=response)
    # TODO: 最好还是要有个全局异常处理器。
    except HTTPException:
        # 已定义的HTTP异常，直接抛出
        raise
    except Exception as e:
        # 未预期的异常，记录日志并返回500错误
        # 安全：不将异常详情返回给客户端，防止信息泄露
        logger.error(f"获取论文时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请联系管理员"
        )


@router.post("/upload/web", response_model=Response[list[PapersUploadResponse]])
async def upload_paper_from_web(
    request: PapersUploadWebRequest,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
):
    """从网络URL直接上传论文"""
    data = await paper_service.upload_papers_from_web(request, current_user.id)
    return Response.success(data=data)


@router.post("/upload", response_model=Response[PaperUploadResponse])
async def upload_paper(
    paper_service: PaperServiceDep,
    file: UploadFile = File(...),
    collection_id: UUID | None = Form(None),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"接收到论文上传请求: filename={file.filename}, user_id={current_user.id}")

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少文件名",
        )

    try:
        file_content = await file.read()
        response = await paper_service.upload_paper(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.id,
            content_type=file.content_type or "application/pdf",
            collection_id=collection_id,
        )
        return Response.success(data=response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"论文上传失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上传失败，请稍后重试",
        )


@router.get("/{paper_id}/status", response_model=Response[PaperStatusResponse])
async def get_paper_status(
    paper_id: str,
    request: Request,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"接收到论文状态查询请求: paper_id={paper_id}, user_id={current_user.id}")

    try:
        paper_uuid = UUID(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的论文ID格式",
        )

    paper = await paper_service.get_paper_status(paper_uuid, current_user.id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无访问权限",
        )
    # TODO:状态用sse发送通知会不会好点
    return Response.success(data=PaperStatusResponse(
        paper_id=str(paper.id),
        status=paper.status.value,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        progress=calculate_progress(paper.status),
        error_message=paper.error_message,
        created_at=paper.created_at,
        updated_at=paper.created_at,
        toc=paper.toc,
        file_url=_resolve_file_url(request, paper.file_url or f"/api/v1/papers/{paper.id}/file")
    ))


@router.post("/{paper_id}/process", response_model=Response[dict], status_code=status.HTTP_202_ACCEPTED)
async def trigger_paper_processing(
    paper_id: str,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
    processing_service: PaperProcessingService = Depends(get_paper_processing_service),
):
    # 解析
    logger.info(f"接收到论文处理触发请求: paper_id={paper_id}, user_id={current_user.id}")

    try:
        paper_uuid = UUID(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的论文ID格式",
        )

    paper = await paper_service.get_paper_status(paper_uuid, current_user.id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无访问权限",
        )

    task = asyncio.create_task(processing_service.process_pdf(paper_uuid))
    task.add_done_callback(_log_background_task_result)
    return Response.success(data={"paper_id": str(paper_uuid), "status": "accepted"})


@router.get("/list", response_model=Response[list[PaperStatusResponse]])
async def list_user_papers(
    request: Request,
    paper_service: PaperServiceDep,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    papers = await paper_service.get_user_papers(user_id=current_user.id, limit=limit, offset=offset)
    return Response.success(data=[
        PaperStatusResponse(
            paper_id=str(p.id),
            status=p.status.value,
            title=p.title,
            authors=p.authors,
            abstract=p.abstract,
            progress=calculate_progress(p.status),
            error_message=p.error_message,
            created_at=p.created_at,
            updated_at=p.created_at,
            toc=p.toc,
            file_url=_resolve_file_url(request, p.file_url)
        )
        for p in papers
    ])


@router.get("/{paper_id}/file")
async def get_paper_file(
    paper_id: str,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"接收到获取论文文件请求: paper_id={paper_id}, user_id={current_user.id}")

    try:
        paper_uuid = UUID(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的论文ID格式",
        )

    paper = await paper_service.get_paper_status(paper_uuid, current_user.id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无访问权限",
        )

    file_path = await paper_service.get_file_path(paper)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件文件不存在",
        )

    download_filename = paper.title
    if not download_filename.lower().endswith(".pdf"):
        download_filename = f"{download_filename}.pdf"

    content_disposition = f"inline; filename*=UTF-8''{quote(download_filename)}"
    use_x_accel = os.getenv("DPRA_USE_X_ACCEL_REDIRECT", "").strip().lower() in {"1", "true", "yes"}
    if use_x_accel:
        internal_uri = f"{INTERNAL_UPLOADS_LOCATION_PREFIX}{paper.file_key}"
        internal_uri = quote(internal_uri, safe="/")
        # TODO:这两种有什么区别嘛?
        return FastAPIResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/pdf",
            headers={
                "X-Accel-Redirect": internal_uri,
                "Content-Disposition": content_disposition,
            },
        )
    # TODO:这两种有什么区别嘛?
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition,
        },
    )


@router.delete("/{paper_id}", response_model=Response[dict])
async def delete_paper(
    paper_id: str,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
):
    try:
        paper_uuid = UUID(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的论文ID格式",
        )

    ok = await paper_service.delete_paper(paper_uuid, current_user.id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无访问权限",
        )
    return Response.success(data={"paper_id": paper_id, "deleted": True})


@router.get("/search/test", response_model=Response[PaperListResponse])
async def test_arxiv_search(
    service: ArxivService = Depends(get_arxiv_service)
):
    '''
    测试接口：获取arXiv最近几篇论文用于测试
    
    使用场景:
    - 前端开发测试
    - API连通性测试
    - 演示功能
    '''

    logger.info("接收到测试请求: 获取arXiv最新论文")

    query = "AI Agent"
    papers = await service.search_papers(query=query, max_results=5)
    
    return Response.success(data=PaperListResponse(
        papers=papers,
        total_count=len(papers),
        source="arXiv",
        fetch_url=f"search: {query}"
    ))


@router.get("/{paper_id}", response_model=Response[PaperStatusResponse])
async def get_paper_by_id(
    paper_id: str,
    request: Request,
    paper_service: PaperServiceDep,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"接收到获取单篇论文请求: paper_id={paper_id}, user_id={current_user.id}")

    try:
        paper_uuid = UUID(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的论文ID格式",
        )

    paper = await paper_service.get_paper_status(paper_uuid, current_user.id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无访问权限",
        )

    return Response.success(data=PaperStatusResponse(
        paper_id=str(paper.id),
        status=paper.status.value,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        progress=calculate_progress(paper.status),
        error_message=paper.error_message,
        created_at=paper.created_at,
        updated_at=paper.created_at,
        toc=paper.toc,
        file_url=_resolve_file_url(request, paper.file_url or f"/api/v1/papers/{paper.id}/file")
    ))
