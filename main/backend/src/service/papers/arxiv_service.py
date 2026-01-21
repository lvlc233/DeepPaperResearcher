'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:重构Service层，使用Infrastructure层（ArxivClient, ArxivXmlParser），符合"3+1"架构]
    [2026年01月02日 08:54:v0.1_arxiv_service:直接调用HTTP和XML解析，违反架构规范]
'''

from loguru import logger
import re
from typing import List

# TODO: 或可统一暴露
from base.arxiv.client import ArxivClient
from base.arxiv.schema import ArxivPaperInfo

from base.arxiv.parser import ArxivXmlParser
from service.papers.schema import PaperInfo

# TODO:后续可能需要扩展为不同类型的通用的URL获取
class ArxivService:
    '''
    arXiv论文获取服务（Service层）

    职责说明:
    - 接收论文URL，提取arXiv ID
    - 调用Base层获取论文元数据
    - 核心业务逻辑：从URL到PaperInfo对象的转换

    设计原则:
    - 符合Service层职责：协调基础设施，实现业务逻辑
    - 不直接处理HTTP请求（由ArxivClient处理）
    - 不直接解析XML（由ArxivXmlParser处理）
    - 依赖注入：接收client和parser作为参数

    使用场景:
    - Controller层需要获取论文信息时调用此服务
    - 整合URL解析、数据获取、XML解析的整个流程

    架构说明:
    - Controller → Service → Infrastructure → External Service
                ↓        ↓
               Data (Business Model)
    '''

    def __init__(self, client: ArxivClient, parser: ArxivXmlParser):
        '''
        初始化arXiv服务

        参数:
        - client: ArxivClient实例，用于获取原始XML数据
        - parser: ArxivXmlParser实例，用于解析XML为PaperInfo

        依赖注入:
        - 通过构造函数注入依赖，便于测试和替换实现
        - 符合依赖倒置原则（DIP）
        '''
        self.client = client
        self.parser = parser
        logger.info("ArxivService 初始化完成，已注入client和parser")


    def extract_arxiv_ids_from_url(self, url: str) -> List[str]:
        '''
        从arXiv URL中提取论文ID列表

        参数:
        - url: arXiv页面URL（搜索页、分类页等）

        返回:
        - arXiv ID列表（如 ['2101.12345', '2102.67890']）

        解析策略:
        1. 解析URL路径
        2. 识别arXiv ID格式（/abs/, /pdf/, 旧格式）
        3. 提取并返回ID列表

        注意:
        - 此方法不调用外部服务，仅解析URL字符串
        - 仅支持单个论文URL，暂不支持搜索页面

        TODO:
        - 未来支持从搜索结果页爬取多个ID
        - 支持批量URL解析
        '''

        logger.info(f"开始从URL提取arXiv ID: {url}")

        arxiv_ids = []

        # 情况1: 直接访问单个论文（格式: /abs/2101.12345 或 /pdf/2101.12345）
        abs_match = re.search(r'/abs/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
        if abs_match:
            arxiv_ids.append(abs_match.group(1))
            logger.info(f"从/abs/路径提取到arXiv ID: {abs_match.group(1)}")

        # 情况2: PDF链接
        pdf_match = re.search(r'/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
        if pdf_match:
            arxiv_ids.append(pdf_match.group(1))
            logger.info(f"从/pdf/路径提取到arXiv ID: {pdf_match.group(1)}")

        # 情况3: 旧格式（如 /abs/hep-th/1234567）
        old_format_match = re.search(r'/abs/([a-z\-]+/\d{7}(?:v\d+)?)', url)
        if old_format_match:
            arxiv_ids.append(old_format_match.group(1))
            logger.info(f"从旧格式路径提取到arXiv ID: {old_format_match.group(1)}")

        # 情况4: 搜索页面（格式: /search/...?query=...）
        # TODO: 实现搜索页面解析，需要爬虫获取页面中的所有论文ID
        if '/search/' in url or 'query?' in url:
            logger.info("检测到搜索页面URL，暂无法直接提取ID，需实现爬虫功能")
            # 未来实现: 使用httpx获取页面内容，解析HTML提取所有arXiv ID

        logger.info(f"从URL提取完成，共获取 {len(arxiv_ids)} 个arXiv ID")
        return arxiv_ids


    async def fetch_papers_from_url(self, url: str) -> List[PaperInfo]:
        '''
        从URL获取论文信息的主入口

        参数:
        - url: arXiv页面URL

        返回:
        - PaperInfo对象列表

        工作流程:
        1. 从URL提取arXiv ID（extract_arxiv_ids_from_url）
        2. 如果提取到ID，调用Base层获取详细数据
        3. 如果没有提取到ID，返回空列表

        架构说明:
        - Service层: 协调处理流程（本方法）
        - Base: 实际的数据获取（client）和解析（parser）

        异常处理:
        - 捕获Base层抛出的异常
        - 记录错误日志，返回空列表（优雅降级）

        TODO:
        - 添加重试机制
        - 添加缓存（Redis）
        '''

        logger.info(f"开始从URL获取论文信息: {url}")

        # 步骤1: 提取arXiv ID
        arxiv_ids = self.extract_arxiv_ids_from_url(url)

        if not arxiv_ids:
            logger.warning(f"无法从URL提取arXiv ID，返回空结果。URL: {url}")
            return []

        # 步骤2: 获取论文详细信息
        try:
            # 调用Infrastructure层获取原始XML
            logger.info("调用Base层（ArxivClient）获取原始XML数据")
            xml_content = await self.client.query_by_ids(arxiv_ids)

            if not xml_content:
                logger.warning("获取到的XML内容为空，返回空列表")
                return []

            # 调用Base层解析XML
            logger.info("调用Base层（ArxivXmlParser）解析XML")
            arxiv_papers: List[ArxivPaperInfo] = self.parser.parse(xml_content)

            logger.info(f"成功获取并解析 {len(arxiv_papers)} 篇论文")

            # 转换为 Service 层 PaperInfo 模型
            # 数据模型转换的那一套避免不了
            papers: List[PaperInfo] = [
                PaperInfo(
                    title=p.title,
                    authors=p.authors,
                    abstract=p.abstract,
                    paper_url=p.paper_url,
                    pdf_url=p.pdf_url,
                    published_date=p.published_date,
                    categories=p.categories,
                    source_id=p.source_id
                ) for p in arxiv_papers
            ]
            
            return papers

        except Exception as e:
            # 捕获所有异常，记录日志，返回空列表（优雅降级）
            logger.error(f"获取或解析论文数据失败: {e}", exc_info=True)
            logger.warning("返回空列表作为降级方案")
            return []


    async def search_papers(self, query: str, start: int = 0, max_results: int = 10) -> List[PaperInfo]:
        '''
        根据关键词搜索arXiv论文 (Service层)

        参数:
        - query: 搜索关键词
        - start: 起始位置
        - max_results: 返回数量

        返回:
        - PaperInfo对象列表
        '''
        logger.info(f"搜索arXiv论文: query='{query}', start={start}, max={max_results}")

        try:
            # 调用Infrastructure层搜索
            xml_content = await self.client.search(query, start, max_results)

            if not xml_content:
                logger.warning("搜索结果为空")
                return []

            # 解析XML
            arxiv_papers: List[ArxivPaperInfo] = self.parser.parse(xml_content)
            logger.info(f"搜索到 {len(arxiv_papers)} 篇论文")

            # 转换为 Service 层 PaperInfo 模型
            papers: List[PaperInfo] = [
                PaperInfo(
                    title=p.title,
                    authors=p.authors,
                    abstract=p.abstract,
                    paper_url=p.paper_url,
                    pdf_url=p.pdf_url,
                    published_date=p.published_date,
                    categories=p.categories,
                    source_id=p.source_id
                ) for p in arxiv_papers
            ]

            return papers

        except Exception as e:
            logger.error(f"搜索论文失败: {e}", exc_info=True)
            return []
