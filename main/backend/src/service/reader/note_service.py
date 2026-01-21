from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from base.pg.entity import Note
from base.pg.service import ReaderRepository
from service.reader.schema import NoteCreateDTO, NoteUpdateDTO, NoteDTO, NoteMeta


class NoteService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notes_by_paper(self, paper_id: UUID, user_id: UUID) -> List[NoteDTO]:
        notes = await ReaderRepository.get_notes_by_paper(self.session, paper_id, user_id)
        return [NoteDTO.model_validate(note) for note in notes]
    
    async def get_notes_meta(self, paper_id: UUID, user_id: UUID) -> List[NoteMeta]:
        notes = await ReaderRepository.get_notes_by_paper(self.session, paper_id, user_id)
        
        items = [
            NoteMeta(
                id=n.id,
                title=n.title,
                page=n.page,
                created_at=n.created_at
            ) for n in notes
        ]
        return items

    async def get_note_detail(self, paper_id: UUID, note_id: UUID, user_id: UUID) -> NoteDTO:
        note = await ReaderRepository.get_note_detail(self.session, paper_id, note_id, user_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
            
        return NoteDTO.model_validate(note)

    async def get_note(self, note_id: UUID, user_id: UUID) -> Optional[Note]:
        return await ReaderRepository.get_note_by_id(self.session, note_id, user_id)

    async def create_note(self, paper_id: UUID, user_id: UUID, note_in: NoteCreateDTO) -> NoteDTO:
        note = Note(
            paper_id=paper_id,
            user_id=user_id,
            title=note_in.title,
            content=note_in.content
        )
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return NoteDTO.model_validate(note)

    async def update_note(self, note_id: UUID, user_id: UUID, note_in: NoteUpdateDTO) -> Optional[NoteDTO]:
        note = await self.get_note(note_id, user_id)
        if not note:
            return None
        
        if note_in.title is not None:
            note.title = note_in.title
        if note_in.content is not None:
            note.content = note_in.content
            
        note.updated_at = datetime.now()
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return NoteDTO.model_validate(note)

    async def delete_note(self, note_id: UUID, user_id: UUID) -> bool:
        note = await self.get_note(note_id, user_id)
        if not note:
            return False
        
        await self.session.delete(note)
        await self.session.commit()
        return True
