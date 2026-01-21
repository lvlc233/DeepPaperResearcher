"""
开发者: BackendAgent
当前版本: v1.0
创建时间: 2026年01月14日
描述: 论文总结服务，负责调用 LLM 生成论文摘要
"""

from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from base.pg.entity import Paper, PaperSummary
from base.pg.service import ReaderRepository, PaperRepository
from service.reader.schema import SummaryCreateDTO, SummaryDTO, AISummary

class SummaryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # TODO: 从配置读取模型参数
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    async def get_ai_summary(self, paper_id: UUID, user_id: UUID) -> Optional[AISummary]:
        summaries = await ReaderRepository.get_summaries_by_paper(self.session, paper_id, user_id)
        
        if not summaries:
            return None
            
        config = {s.summary_type: s.content for s in summaries}
        return AISummary(summary_config=config)

    async def get_summary(self, paper_id: UUID, summary_type: str) -> Optional[SummaryDTO]:
        """获取论文摘要"""
        summary = await ReaderRepository.get_summary_by_type(self.session, paper_id, summary_type)
        
        if summary:
            return SummaryDTO.model_validate(summary)
        return None

    async def get_or_create_summary(self, paper_id: UUID, create_in: SummaryCreateDTO) -> SummaryDTO:
        """获取或生成论文摘要"""
        # 1. 检查是否存在已有摘要
        summary = await ReaderRepository.get_summary_by_type(self.session, paper_id, create_in.summary_type)
        
        if summary:
            return SummaryDTO.model_validate(summary)

        # 2. 获取论文内容
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )

        # 3. 生成摘要
        content = await self._generate_summary_content(paper, create_in.summary_type)
        
        # 4. 保存摘要
        new_summary = PaperSummary(
            paper_id=paper_id,
            summary_type=create_in.summary_type,
            content=content
        )
        self.session.add(new_summary)
        await self.session.commit()
        await self.session.refresh(new_summary)
        
        return SummaryDTO.model_validate(new_summary)

    # TODO: 这里等Agent实现吧。
    async def _generate_summary_content(self, paper: Paper, summary_type: str) -> str:
        """调用 LLM 生成摘要内容"""
        
        # 准备上下文: 优先使用摘要，如果没有则提示用户无法生成(或者后续扩展读取 chunks)
        context = paper.abstract
        if not context:
            # TODO: 如果 abstract 为空，尝试读取 paper chunks (需要 PaperChunk 关联查询)
            # 暂时返回占位符或报错
            return "无法生成摘要: 论文缺少摘要信息且未实现全文读取。"

        # 定义 Prompt
        if summary_type == "abstract_rewrite":
            system_prompt = "你是一个专业的学术论文助手。请将以下论文摘要重写为通俗易懂的中文总结，保留核心观点。"
        elif summary_type == "key_points":
            system_prompt = "你是一个专业的学术论文助手。请提取以下论文摘要的3-5个关键创新点，使用Markdown列表格式。"
        elif summary_type == "methodology":
            system_prompt = "你是一个专业的学术论文助手。请专注于分析以下内容中的研究方法和技术路线。"
        else:
            system_prompt = "你是一个专业的学术论文助手。请总结以下内容。"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "论文标题: {title}\n\n内容:\n{context}")
        ])

        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "title": paper.title,
                "context": context
            })
            return response.content
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summary generation failed: {str(e)}"
            )
