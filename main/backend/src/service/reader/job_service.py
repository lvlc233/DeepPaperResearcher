import asyncio
import json
from datetime import datetime
from typing import List, AsyncGenerator, Optional, Any
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from base.pg.entity import Job, Paper
from service.reader.schema import Job as JobDTO, JobResult
from controller.api.reader.schema import JobCreateRequest, JobResponse, SSEDataEnvelope, JobEventPayload


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_jobs(self, paper_id: UUID, user_id: UUID) -> List[JobDTO]:
        # Job does not have user_id, join Paper
        stmt = (
            select(Job)
            .join(Paper)
            .where(Job.paper_id == paper_id, Paper.user_id == user_id)
            .order_by(Job.created_at.desc())
        )
        result = await self.session.execute(stmt)
        jobs = result.scalars().all()
        
        items = [
            JobDTO(
                id=j.id,
                job_type=j.job_type,
                status=j.status,
                progress=float(j.progress) if j.progress is not None else 0.0,
                stage=j.stage,
                error_message=j.error_message,
                created_at=j.created_at,
                completed_at=j.completed_at,
                result=j.result # Assuming result is stored as JSON and compatible with JobResult
            ) for j in jobs
        ]
        return items

    async def create_job(self, paper_id: UUID, req: JobCreateRequest, user_id: UUID) -> JobResponse:
        # Check paper permission
        stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
        result = await self.session.execute(stmt)
        paper = result.scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Create Job
        new_job = Job(
            id=uuid4(),
            paper_id=paper_id,
            job_type=req.job_type,
            status="queued",
            progress=0,
            params=req.params,
            created_at=datetime.now()
        )
        self.session.add(new_job)
        await self.session.commit()
        await self.session.refresh(new_job)
        
        # TODO: Trigger background task here
        # For example: task_service.submit(new_job.id)
        
        return JobResponse.model_validate(new_job)

    async def get_job(self, job_id: UUID, user_id: UUID) -> JobResponse:
        # Join Paper to check user permission
        stmt = (
            select(Job)
            .join(Paper)
            .where(Job.id == job_id, Paper.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse.model_validate(job)

    async def subscribe_job_events(self, job_id: UUID, user_id: UUID) -> AsyncGenerator[str, None]:
        # 1. Check permission
        await self.get_job(job_id, user_id)

        # 2. Simulate SSE (In production, use Redis Pub/Sub)
        # Mocking progress for demonstration since we don't have real backend workers connected yet
        try:
            # Send Start
            yield self._format_sse("start", job_id, "queued", 0, "Job started")
            
            # Mock progress
            for i in range(1, 6):
                await asyncio.sleep(1)
                yield self._format_sse("progress", job_id, "running", i * 20, f"Processing step {i}")
            
            # Send End
            yield self._format_sse("end", job_id, "succeeded", 100, "Job completed", result={"summary": "Done"})
            
        except Exception as e:
            yield self._format_sse("error", job_id, "failed", 0, str(e))

    def _format_sse(self, state: str, job_id: UUID, status: str, progress: float, stage: str, result: Any = None, error: str = None) -> str:
        payload = JobEventPayload(
            job_id=job_id,
            type="unknown", # Should retrieve type from job if possible, or pass it in
            status=status,
            progress=progress,
            stage=stage,
            result=result,
            error=error
        )
        envelope = SSEDataEnvelope(
            state=state,
            payload=payload
        )
        return f"id: {uuid4()}\nevent: Job{state.capitalize()}\ndata: {envelope.model_dump_json()}\n\n"
