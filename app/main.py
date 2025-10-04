from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from . import crud
from .config import settings
from .database import engine, init_db
from .models import JobStatus, VideoJob
from .schemas import VideoJobCreateForm, VideoJobList, VideoJobRead
from .storage import as_public_path, resolve_output_path, save_upload_file

logger = logging.getLogger(__name__)

app = FastAPI(title="Image-to-Video Clone API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("api.startup")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/health", tags=["health"])
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/videos", response_model=VideoJobRead, status_code=202)
async def create_video_job(
    payload: VideoJobCreateForm = Depends(VideoJobCreateForm.as_form),
    image: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> VideoJobRead:
    job_id = uuid.uuid4()
    input_path = await save_upload_file(image, job_id)
    video_job = VideoJob(
        id=job_id,
        prompt=payload.prompt,
        duration_seconds=payload.duration_seconds or settings.default_duration_seconds,
        fps=payload.fps or settings.default_fps,
        effect=payload.effect,
        seed=payload.seed,
        status=JobStatus.queued,
        input_path=str(input_path),
        output_path=str(resolve_output_path(job_id)),
    )

    created = crud.create_job(session, video_job)
    logger.info("api.job_created job_id=%s", created.id)
    return VideoJobRead.model_validate(created)


@app.get("/api/v1/videos/{job_id}", response_model=VideoJobRead)
def get_video_job(job_id: uuid.UUID, session: Session = Depends(get_session)) -> VideoJobRead:
    job = crud.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return VideoJobRead.model_validate(job)


@app.get("/api/v1/videos", response_model=VideoJobList)
def list_video_jobs(limit: int = 50, offset: int = 0, session: Session = Depends(get_session)) -> VideoJobList:
    jobs = list(crud.list_jobs(session, limit=limit, offset=offset))
    total = crud.count_jobs(session)
    return VideoJobList(items=[VideoJobRead.model_validate(job) for job in jobs], total=total)


@app.get("/api/v1/videos/{job_id}/artifact")
def download_artifact(job_id: uuid.UUID, session: Session = Depends(get_session)) -> JSONResponse:
    job = crud.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.completed or not job.output_path:
        raise HTTPException(status_code=409, detail="Job is not yet complete")

    return JSONResponse({"path": as_public_path(Path(job.output_path))})

