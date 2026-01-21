from typing import List
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.service import ReaderRepository
from service.reader.schema import Record, Message

class HistoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ai_history(self, paper_id: UUID, user_id: UUID) -> List[Record]:
        sessions = await ReaderRepository.get_history_by_paper(self.session, paper_id, user_id)
        
        return [
            Record(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in sessions
        ]

    async def get_record_detail(self, paper_id: UUID, record_id: UUID, user_id: UUID) -> List[Message]:
        session = await ReaderRepository.get_session_detail(self.session, paper_id, record_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Record not found")
            
        return []
