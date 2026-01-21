'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:创建arXiv XML解析器（Infrastructure层），负责解析arXiv返回的XML数据]
'''

import re
import xml.etree.ElementTree as ET
from typing import List

from base.arxiv.schema import ArxivPaperInfo

# 配置日志
from loguru import logger


# pdf解析
class ArxivXmlParser:
    '''
    arXiv XML 解析器（Infrastructure层）

    职责说明:
    - 解析arXiv API返回的XML格式数据
    - 提取论文元数据并转换为业务模型（ArxivPaperInfo）
    - 仅处理数据格式转换，不包含业务逻辑

    设计原则:
    - 符合Infrastructure层职责，专门处理数据格式
    - 输入：原始XML字符串
    - 输出：标准化的ArxivPaperInfo对象列表
    - 异常处理：解析错误时返回空列表，而不是抛出异常

    使用场景:
    - Service层获取到XML后，调用此解析器转换为业务对象
    - 所有XML解析逻辑都集中在此，便于维护
    '''

    def __init__(self):
        '''初始化解析器'''
        logger.info("ArxivXmlParser 初始化完成")


    def parse(self, xml_content: str) -> List[ArxivPaperInfo]:
        '''
        解析arXiv API返回的XML数据

        参数:
        - xml_content: arXiv API返回的原始XML字符串

        返回:
        - ArxivPaperInfo对象列表

        实现逻辑:
        1. 解析XML命名空间
        2. 遍历所有entry（论文条目）
        3. 提取每个论文的字段信息
        4. 创建PaperInfo对象
        5. 返回结果列表

        异常处理:
        - XML解析失败：记录错误日志，返回空列表
        - 单篇论文解析失败：记录警告，继续解析下一篇
        - 缺少必填字段：使用默认值，保证程序不崩溃

        TODO:
        - XML格式校验（XSD）
        - 字段缺失时的默认值策略优化
        - 性能优化（大批量XML解析）
        '''

        if not xml_content or not xml_content.strip():
            logger.warning("XML内容为空，返回空列表")
            return []

        papers = []
 
        try:
          
            # 解析XML，处理命名空间
            root = ET.fromstring(xml_content)
            namespace = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            # debug
            logger.info(f"XML命名空间: {xml_content}")
            logger.info("开始解析XML，查找论文条目")

            # 遍历所有论文条目
            for entry in root.findall('atom:entry', namespace):
                try:
                    # 提取论文信息
                    paper = self._parse_entry(entry, namespace)
                    if paper:
                        papers.append(paper)
                        logger.debug(f"成功解析论文: {paper.title[:50]}...")

                except Exception as e:
                    # 单篇论文解析失败，记录警告，继续解析下一篇
                    logger.warning(f"解析单篇论文信息失败，跳过: {e}", exc_info=True)
                    continue

            logger.info(f"XML解析完成，成功解析 {len(papers)} 篇论文")

        except ET.ParseError as e:
            logger.error(f"XML解析失败，格式错误: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"解析arXiv XML时发生未知错误: {e}", exc_info=True)

        return papers


    def _parse_entry(self, entry, namespace) -> ArxivPaperInfo:
        '''
        解析单个论文条目

        参数:
        - entry: XML中的entry元素
        - namespace: XML命名空间字典

        返回:
        - ArxivPaperInfo对象，如果解析失败返回None
        '''

        # 提取标题
        title_elem = entry.find('atom:title', namespace)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

        # 提取作者列表
        authors = []
        for author in entry.findall('atom:author', namespace):
            name_elem = author.find('atom:name', namespace)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())

        # 提取摘要
        summary_elem = entry.find('atom:summary', namespace)
        summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""

        # 提取arXiv ID（从id字段）
        entry_id_elem = entry.find('atom:id', namespace)
        arxiv_id = ""
        if entry_id_elem is not None and entry_id_elem.text:
            # 格式: http://arxiv.org/abs/2101.12345
            id_match = re.search(r'/abs/(\d{4}\.\d{4,5}(?:v\d+)?)$', entry_id_elem.text)
            if id_match:
                arxiv_id = id_match.group(1)

        # 生成PDF链接
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

        # 提取发表日期
        published_elem = entry.find('atom:published', namespace)
        published_date = published_elem.text if published_elem is not None else None

        # 提取分类
        categories = []
        for category in entry.findall('atom:category', namespace):
            term = category.get('term')
            if term:
                categories.append(term)

        # 创建ArxivPaperInfo对象
        # 必填字段必须有值（title, authors, abstract）
        if not title:
            logger.warning("论文标题为空，可能数据不完整")

        if not authors:
            logger.warning("作者列表为空，可能数据不完整")

        if not summary:
            logger.warning("摘要为空，可能数据不完整")

        paper = ArxivPaperInfo(
            title=title,
            authors=authors,
            abstract=summary,
            paper_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            pdf_url=pdf_url,
            published_date=published_date,
            categories=categories,
            source_id=arxiv_id
        )

        return paper
