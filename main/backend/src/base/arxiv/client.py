'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:创建arXiv客户端，负责与arXiv API通信（Infrastructure层）]
'''

import httpx
from typing import List
from loguru import logger

# 备注: 网络相关和pdf解析无关
class ArxivClient:
    '''
    arXiv API 客户端（Base层）

    职责说明:
    - 负责与arXiv外部API进行HTTP通信
    - 返回原始XML响应字符串
    - 处理网络错误、超时等基础设施相关问题
    - 不处理业务逻辑，只处理数据传输

    设计原则:
    - 符合Base层职责，不依赖Service层
    - 返回原始数据，由上层解析
    - 统一的错误处理和重试机制（TODO）

    使用场景:
    - Service层需要获取arXiv数据时，调用此客户端
    - 所有与arXiv的网络交互都经过此客户端
    '''

    def __init__(self, base_url: str = "https://export.arxiv.org/api/query"):
        '''
        初始化arXiv客户端

        参数:
        - base_url: arXiv API的基础URL，默认可配置
        '''
        self.base_url = base_url
        self.headers = {
            "User-Agent": "DeepResearcher/0.1 (Contact: backend@research.local)"
        }
        self.timeout = 30.0  # 请求超时时间（秒）

        logger.info(f"ArxivClient 初始化完成，基础URL: {self.base_url}")

    
    async def query_by_ids(self, arxiv_ids: List[str]) -> str:
        '''
        通过arXiv ID列表查询论文元数据
        
        参数:
        - arxiv_ids: arXiv ID列表，如 ["2101.12345", "2102.67890"]
        
        返回:
        - 原始XML字符串（arXiv API返回的原始响应）
        
        异常:
        - HTTPError: 当arXiv API返回错误状态码时
        - TimeoutError: 当请求超时时
        - RequestError: 网络连接等其他错误
        
        实现逻辑:
        1. 构建查询参数（id_list）
        2. 发送异步HTTP GET请求
        3. 检查响应状态码
        4. 返回原始响应文本
        
        TODO:
        - 添加重试机制（指数退避）
        - 添加请求缓存（Redis）
        - 添加请求速率限制（防止被封禁）
        - 支持批量查询的分页处理（如果ID过多）
        '''

        if not arxiv_ids:
            logger.warning("arXiv ID列表为空，返回空字符串")
            return ""

        logger.info(f"开始查询arXiv，共 {len(arxiv_ids)} 个ID")

        # 构建查询参数
        params = {
            "id_list": ",".join(arxiv_ids),
            "max_results": len(arxiv_ids)
        }

        return await self._execute_query(params)

    async def search(self, query: str, start: int = 0, max_results: int = 10) -> str:
        '''
        根据关键词搜索arXiv论文
        
        参数:
        - query: 搜索关键词 (如 "machine learning")
        - start: 分页起始位置
        - max_results: 返回结果数量
        
        返回:
        - 原始XML字符串
        '''
        logger.info(f"开始搜索arXiv: query='{query}', start={start}, max={max_results}")
        
        params = {
            "search_query": f"all:{query}",
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        return await self._execute_query(params)

    async def _execute_query(self, params: dict) -> str:
        '''
        执行arXiv API查询的通用方法
        '''
        try:
            # 发送HTTP请求
            logger.debug(f"发送HTTP请求: {self.base_url}, 参数: {params}")

            # 使用异步HTTP客户端
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                )

                # 检查响应状态码
                response.raise_for_status()

                # 返回原始XML文本
                xml_content = response.text
                logger.info(f"成功获取响应，内容长度: {len(xml_content)} 字符")
                return xml_content

        except httpx.HTTPStatusError as e:
            # HTTP错误（4xx, 5xx）
            logger.error(f"arXiv API返回错误状态码: {e.response.status_code}, URL: {e.request.url}", exc_info=True)
            # 重新抛出，由上层处理
            raise

        except httpx.TimeoutException as e:
            # 超时错误
            logger.error(f"请求arXiv API超时（{self.timeout}秒）", exc_info=True)
            raise

        except httpx.RequestError as e:
            # 其他请求错误（网络连接等）
            logger.error(f"请求arXiv API失败: {e}", exc_info=True)
            raise

        except Exception as e:
            # 未知错误
            logger.error(f"查询arXiv时发生未知错误: {e}", exc_info=True)
            raise
