from __future__ import annotations

import logging
import time
from contextlib import suppress

from sqlalchemy.exc import OperationalError

from .config import settings
from .crud import next_queued_jobs
from .database import init_db, session_scope
from .models import JobStatus, VideoJob
from .video_pipeline import VideoGenerationError, generate_video

logger = logging.getLogger(__name__)


def _process_job(job: VideoJob) -> None:
    logger.info("worker.start job_id=%s", job.id)
    job.status = JobStatus.processing
    job.touch()

    output_path = generate_video(job)

    job.output_path = str(output_path)
    job.status = JobStatus.completed
    job.touch()
    logger.info("worker.complete job_id=%s output_path=%s", job.id, job.output_path)


def _fail_job(job: VideoJob, error: Exception) -> None:
    job.status = JobStatus.failed
    job.error_message = str(error)
    job.touch()
    logger.exception("worker.error job_id=%s error=%s", job.id, error)


def worker_loop() -> None:
    init_db()
    logger.info("worker.boot poll_interval=%s", settings.job_poll_interval)

    while True:
        with session_scope() as session:
            jobs = next_queued_jobs(session, settings.worker_batch_size)
            if not jobs:
                time.sleep(settings.job_poll_interval)
                continue

            for job in jobs:
                try:
                    _process_job(job)
                except (VideoGenerationError, RuntimeError, ValueError) as error:
                    _fail_job(job, error)
                except Exception as error:  # pragma: no cover - unexpected failure logging
                    _fail_job(job, error)
                finally:
                    session.add(job)
                    with suppress(OperationalError):
                        session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker_loop()

