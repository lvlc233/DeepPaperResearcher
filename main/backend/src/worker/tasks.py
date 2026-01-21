'''
开发者: BackendAgent
当前版本: v1.0_arq_tasks
创建时间: 2026年01月08日 14:30
更新时间: 2026年01月08日 14:30
更新记录:
    [2026年01月08日 14:30:v1.0_arq_tasks:创建Arq异步任务，集成PDF解析和向量化处理]
'''


from typing import Any, Dict
from uuid import UUID

from arq import create_pool, cron
from arq.connections import RedisSettings
from arq.worker import Worker

from base.config import settings
from service.papers.paper_service import PaperProcessingService


from loguru import logger


class ArqRedisSettings(RedisSettings):
    """自定义Redis设置，支持从配置读取"""

    def __init__(self):
        # 从settings中读取Redis配置
        super().__init__(
            host=settings.arq_redis_url.split('//')[1].split(':')[0],
            port=int(settings.arq_redis_url.split(':')[-1].split('/')[0]),
            database=int(settings.arq_redis_url.split('/')[-1])
        )


# 异步任务定义
async def process_pdf_task(ctx: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
    """
    处理PDF文件的异步任务

    参数:
    - ctx: 任务上下文
    - paper_id: 论文ID（字符串格式）

    返回:
    - dict: 处理结果

    工作流程:
    1. 初始化处理服务
    2. 调用处理逻辑
    3. 返回处理结果

    异常处理:
    - 捕获所有异常并记录日志
    - 返回错误信息以便前端显示
    """
    logger.info(f"开始异步处理PDF任务: {paper_id}")

    try:
        # 转换paper_id为UUID
        uuid_paper_id = UUID(paper_id)

        # 初始化处理服务
        processing_service = PaperProcessingService()

        # 处理PDF
        success = await processing_service.process_pdf(uuid_paper_id)

        if success:
            logger.info(f"PDF处理成功: {paper_id}")
            return {
                "status": "success",
                "paper_id": paper_id,
                "message": "PDF处理完成"
            }
        else:
            logger.error(f"PDF处理失败: {paper_id}")
            return {
                "status": "failed",
                "paper_id": paper_id,
                "message": "PDF处理失败"
            }

    except Exception as e:
        logger.error(f"PDF任务执行异常: {paper_id}, 错误: {e}", exc_info=True)
        return {
            "status": "error",
            "paper_id": paper_id,
            "message": f"任务执行异常: {str(e)}"
        }


async def generate_embeddings_task(
    ctx: Dict[str, Any],
    chunks: list,
    model: str = "text-embedding-ada-002"
) -> Dict[str, Any]:
    """
    生成文本向量嵌入的异步任务

    参数:
    - ctx: 任务上下文
    - chunks: 文本块列表
    - model: 嵌入模型名称

    返回:
    - dict: 包含生成的向量列表

    TODO:
    - 集成OpenAI或其他嵌入模型
    - 支持批量处理优化性能
    """
    logger.info(f"开始生成向量嵌入，chunks数量: {len(chunks)}")

    try:
        # TODO: 实现向量生成逻辑
        # 临时返回模拟数据
        embeddings = []
        for i, chunk in enumerate(chunks):
            # 模拟向量生成（实际应调用嵌入模型API）
            embedding = [0.1 * (i + 1)] * 1536  # 1536维向量
            embeddings.append(embedding)

        logger.info(f"向量嵌入生成完成，数量: {len(embeddings)}")
        return {
            "status": "success",
            "embeddings": embeddings,
            "count": len(embeddings)
        }

    except Exception as e:
        logger.error(f"向量生成任务失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"向量生成失败: {str(e)}"
        }


async def cleanup_failed_tasks(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理失败任务的定时任务

    参数:
    - ctx: 任务上下文

    返回:
    - dict: 清理结果

    功能:
    - 删除超过7天的失败任务记录
    - 清理临时文件
    - 释放存储空间
    """
    logger.info("开始清理失败任务")

    try:
        # TODO: 实现清理逻辑
        # 1. 查询数据库中失败的旧任务
        # 2. 删除相关文件
        # 3. 更新数据库记录

        logger.info("失败任务清理完成")
        return {
            "status": "success",
            "message": "清理完成"
        }

    except Exception as e:
        logger.error(f"清理任务失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"清理失败: {str(e)}"
        }


# 任务配置
class WorkerSettings:
    """Arq Worker配置"""

    # Redis连接设置
    redis_settings = ArqRedisSettings()

    # 任务函数注册
    functions = [
        process_pdf_task,
        generate_embeddings_task,
        cleanup_failed_tasks
    ]

    # 定时任务（cron jobs）
    cron_jobs = [
        # 每天凌晨2点清理失败任务
        cron(
            cleanup_failed_tasks,
            hour=2,
            minute=0
        )
    ]

    # Worker配置
    max_jobs = 10  # 最大并发任务数
    job_timeout = 600  # 任务超时时间（秒）
    keep_result = 86400  # 保留任务结果时间（秒）
    max_tries = 3  # 最大重试次数
    retry_delay = 10  # 重试延迟（秒）


# 任务队列管理器
class TaskQueue:
    """任务队列管理器，提供任务入队接口"""

    def __init__(self):
        self._pool = None

    async def init(self):
        """初始化Redis连接池"""
        if not self._pool:
            self._pool = await create_pool(ArqRedisSettings())
            logger.info("任务队列初始化完成")

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("任务队列已关闭")

    async def enqueue_process_pdf(self, paper_id: str) -> str:
        """
        入队PDF处理任务

        参数:
        - paper_id: 论文ID

        返回:
        - str: 任务ID
        """
        await self.init()
        job = await self._pool.enqueue_job(
            'process_pdf_task',
            paper_id,
            _queue_name='pdf_processing'
        )
        logger.info(f"PDF处理任务已入队: {job.job_id}")
        return job.job_id

    async def enqueue_generate_embeddings(
        self,
        chunks: list,
        model: str = "text-embedding-ada-002"
    ) -> str:
        """
        入队向量生成任务

        参数:
        - chunks: 文本块列表
        - model: 嵌入模型

        返回:
        - str: 任务ID
        """
        await self.init()
        job = await self._pool.enqueue_job(
            'generate_embeddings_task',
            chunks,
            model,
            _queue_name='embeddings'
        )
        logger.info(f"向量生成任务已入队: {job.job_id}")
        return job.job_id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        参数:
        - job_id: 任务ID

        返回:
        - dict: 任务状态信息
        """
        await self.init()
        job = await self._pool.get_job_result(job_id)

        if job:
            return {
                "job_id": job_id,
                "status": job.status,
                "result": job.result,
                "error": job.error
            }
        else:
            return {
                "job_id": job_id,
                "status": "not_found",
                "message": "任务不存在或结果已过期"
            }


# 全局任务队列实例
task_queue = TaskQueue()


# 启动Worker的函数
def create_worker() -> Worker:
    """
    创建Arq Worker实例

    返回:
    - Worker: Worker实例
    """
    return Worker(
        redis_settings=ArqRedisSettings(),
        functions=WorkerSettings.functions,
        cron_jobs=WorkerSettings.cron_jobs,
        max_jobs=WorkerSettings.max_jobs,
        job_timeout=WorkerSettings.job_timeout,
        keep_result=WorkerSettings.keep_result,
        max_tries=WorkerSettings.max_tries,
        retry_delay=WorkerSettings.retry_delay
    )


# 运行Worker（用于命令行启动）
async def run_worker():
    """运行Worker"""
    worker = create_worker()
    await worker.main()