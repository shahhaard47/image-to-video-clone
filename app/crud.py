from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import func
from sqlmodel import Session, select

from .models import JobStatus, VideoJob


def create_job(session: Session, job: VideoJob) -> VideoJob:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: uuid.UUID) -> VideoJob | None:
    return session.get(VideoJob, job_id)


def list_jobs(session: Session, limit: int = 50, offset: int = 0) -> Iterable[VideoJob]:
    statement = select(VideoJob).order_by(VideoJob.created_at.desc()).offset(offset).limit(limit)
    return session.exec(statement)


def count_jobs(session: Session) -> int:
    statement = select(func.count()).select_from(VideoJob)
    result = session.exec(statement).one()
    return int(result or 0)


def next_queued_jobs(session: Session, limit: int) -> list[VideoJob]:
    statement = (
        select(VideoJob)
        .where(VideoJob.status == JobStatus.queued)
        .order_by(VideoJob.created_at)
        .limit(limit)
    )

    if session.bind and session.bind.dialect.name not in {"sqlite"}:
        statement = statement.with_for_update(skip_locked=True)

    return list(session.exec(statement))

