"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的工具定义，包含 Arxiv 搜索与论文读取能力 (异步实现)。
更新记录:
    [2026-01-05:v1.1:迁移至 httpx 实现全异步 IO]
"""
import xml.etree.ElementTree as ET
import urllib.parse
import httpx
from typing import List, Dict, Any
from langchain_core.tools import tool

@tool
async def internet_search(query: str) -> str:
    """
    在 Arxiv 上执行搜索。
    返回搜索结果摘要，包括标题、作者和摘要。
    """
    base_url = "http://export.arxiv.org/api/query?"
    # 简单的查询构建
    search_query = f"all:{query}"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": 5
    }
    url = base_url + urllib.parse.urlencode(params)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.content
            
        root = ET.fromstring(data)
        
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []
        
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
            id_url = entry.find('atom:id', namespace).text.strip()
            
            authors = []
            for author in entry.findall('atom:author', namespace):
                name = author.find('atom:name', namespace).text
                authors.append(name)
            
            results.append(f"标题: {title}\n作者: {', '.join(authors)}\n链接: {id_url}\n摘要: {summary[:200]}...\n")
        
        if not results:
            return f"在 Arxiv 上未找到关于以下查询的结果: {query}"
        
        return "\n---\n".join(results)
        
    except Exception as e:
        return f"Arxiv 搜索出错: {str(e)}"

@tool
async def read_paper(url: str) -> str:
    """
    从给定的 Arxiv URL 读取研究论文的详细信息。
    注意：目前返回完整的摘要/简介作为论文内容。
    """
    # 提取 Arxiv ID
    # URL 格式通常为 http://arxiv.org/abs/2310.12345 或 http://arxiv.org/pdf/2310.12345
    try:
        arxiv_id = url.split('/')[-1].replace('.pdf', '')
        
        base_url = "http://export.arxiv.org/api/query?"
        params = {
            "id_list": arxiv_id
        }
        api_url = base_url + urllib.parse.urlencode(params)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, timeout=30.0)
            response.raise_for_status()
            data = response.content

        root = ET.fromstring(data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entry = root.find('atom:entry', namespace)
        if entry is None:
            return f"未找到 URL 对应的论文: {url}"
            
        title = entry.find('atom:title', namespace).text.strip()
        summary = entry.find('atom:summary', namespace).text.strip()
        published = entry.find('atom:published', namespace).text.strip()
        
        return f"标题: {title}\n发布时间: {published}\n\n完整摘要:\n{summary}"

    except Exception as e:
        return f"读取论文出错: {str(e)}"

# 导出工具列表
tools = [internet_search, read_paper]
