# System Architecture

This document describes the initial implementation of the Vidnoz Image-to-Video clone. It is intentionally practical: a developer can run the service locally, extend it with new effects, and deploy it in containers without significant rework.

## High-Level Overview

The system is composed of three primary concerns:

1. **REST API (FastAPI)** – accepts uploads, persists job metadata, and surfaces status/results.
2. **Worker** – polls for queued jobs and converts still images into motion videos using MoviePy.
3. **Artifact Storage** – stores user uploads and generated videos on disk (default) or any mounted volume.

SQLite is used for default persistence to minimize setup friction. The abstraction layer (SQLModel over SQLAlchemy) keeps the door open for PostgreSQL/MySQL by changing the `APP_DATABASE_URL` environment variable.

```
+-----------+        POST /videos        +-----------------+
|  Client   | -------------------------> |  FastAPI Server |
+-----------+                           +-----------------+
        ^                                         |
        |                              writes job | metadata
        |                                         v
        |                                +----------------+
        |                                |   SQLite DB    |
        |                                +----------------+
        |                                         |
        |<-------------- polling -----------------+
        |                                         v
        |                                +----------------+
        |                                |   Worker       |
        |                                +----------------+
        |                                         |
        |<-------------- artifact path -----------+
```

## Job Lifecycle

1. Client uploads an image (`multipart/form-data`) with optional metadata.
2. API stores the image on disk and creates a `VideoJob` row with status `queued`.
3. Worker periodically fetches queued jobs, flips them to `processing`, and generates an MP4 using a Ken Burns-style pan/zoom.
4. Worker marks the job as `completed` (or `failed`) and writes the artifact path back to the database.
5. Client polls `/api/v1/videos/{id}` for status or `/api/v1/videos/{id}/artifact` once completed.

## Technology Choices

- **FastAPI** – lightweight, async capable, automatically generates OpenAPI/Swagger docs. Compatible with modern Python typing.
- **SQLModel** – SQLAlchemy core with Pydantic-style models. Low ceremony and easy to swap database engines.
- **MoviePy + Pillow** – proven video manipulation libraries. MoviePy writes MP4 using FFmpeg (bundled via `imageio-ffmpeg`).
- **Structlog-style JSON logging (via `extra=` fields)** – provides structured context without enforcing a logging backend.
- **Docker + Compose** – reproducible runtime with FFmpeg dependency pre-installed.

## Extensibility Hooks

- New effects can be introduced by adding functions to `app/video_pipeline.py` and persisting the chosen effect in the `VideoJob.effect` column.
- Storage can be swapped by replacing `app/storage.py` helpers (e.g., upload to S3) while keeping the API surface intact.
- Background processing can be scaled horizontally by running multiple worker containers; optimistic locking is used when supported by the database.

## Operational Considerations

- **Idempotency**: Worker only transitions `queued` jobs. If a worker crashes mid-run, the status remains `processing`; administrators can reset via SQL.
- **Observability**: Logs include job IDs, poll intervals, and errors. Plug into log aggregation (e.g., ELK, Grafana Loki) for production.
- **Scaling**: Move to PostgreSQL and configure a shared file system (e.g., S3 + signed URLs) for larger deployments. Introduce a real queue (Celery/RabbitMQ) once throughput demands it.
- **Security**: Auth is intentionally out of scope for MVP. Add API keys/JWT + signed artifact URLs before exposing publicly.

