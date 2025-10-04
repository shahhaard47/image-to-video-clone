from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field

from .models import JobStatus


class VideoJobBase(BaseModel):
    prompt: Optional[str] = None
    duration_seconds: float = Field(default=5.0, gt=0)
    fps: int = Field(default=24, ge=12, le=60)
    effect: str = Field(default="kenburns")
    seed: Optional[int] = Field(default=None, ge=0)


class VideoJobCreate(VideoJobBase):
    pass


class VideoJobCreateForm(VideoJobCreate):
    @classmethod
    def as_form(
        cls,
        prompt: Optional[str] = Form(default=None),
        duration_seconds: float = Form(default=5.0),
        fps: int = Form(default=24),
        effect: str = Form(default="kenburns"),
        seed: Optional[int] = Form(default=None),
    ) -> "VideoJobCreateForm":
        return cls(
            prompt=prompt,
            duration_seconds=duration_seconds,
            fps=fps,
            effect=effect,
            seed=seed,
        )


class VideoJobRead(VideoJobBase):
    id: uuid.UUID
    status: JobStatus
    output_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoJobList(BaseModel):
    items: list[VideoJobRead]
    total: int

