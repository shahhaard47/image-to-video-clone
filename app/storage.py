from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from .config import settings


async def save_upload_file(file: UploadFile, job_id: uuid.UUID) -> Path:
    suffix = Path(file.filename or "").suffix or ".png"
    destination = settings.upload_dir / f"{job_id}{suffix}"

    await file.seek(0)
    async with aiofiles.open(destination, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await buffer.write(chunk)
    await file.seek(0)
    return destination


def resolve_output_path(job_id: uuid.UUID, extension: str = "mp4") -> Path:
    return settings.output_dir / f"{job_id}.{extension}"


def as_public_path(path: Path) -> str:
    return str(path.resolve())

