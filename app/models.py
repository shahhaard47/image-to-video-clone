from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class VideoJob(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    prompt: Optional[str] = Field(default=None)
    status: JobStatus = Field(default=JobStatus.queued)
    input_path: str = Field(index=False, nullable=False)
    output_path: Optional[str] = Field(default=None, nullable=True)
    duration_seconds: float = Field(default=5.0, nullable=False)
    fps: int = Field(default=24, nullable=False)
    effect: str = Field(default="kenburns", nullable=False)
    seed: Optional[int] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

