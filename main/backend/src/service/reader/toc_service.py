from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.entity import Paper
from service.reader.schema import Toc, TocItem


class TocService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_toc(self, paper_id: UUID, user_id: UUID) -> Toc:
        stmt = select(Paper.toc).where(Paper.id == paper_id, Paper.user_id == user_id)
        result = await self.session.execute(stmt)
        toc_data = result.scalar_one_or_none()
        
        if toc_data is None: 
             # Check if paper exists first if strict 404 is needed
             # For now, consistent with previous logic
             raise HTTPException(status_code=404, detail="Paper not found or TOC empty")
             
        items = [TocItem(**item) for item in toc_data]
        return Toc(items=items)
