# Image-to-Video AI Clone

Production-ready starter implementation for a Vidnoz-style image-to-video generator. The service accepts an image upload, queues it for processing, renders a short Ken Burns-style motion clip, and exposes the artifact path through a REST API.

The repository now contains everything required to run locally with Python, in Docker, or inside CI. Extensive documentation is included under `docs/`.

## Contents

- [`app/`](app/) – FastAPI application, worker loop, persistence models, and video generation pipeline.
- [`docs/architecture.md`](docs/architecture.md) – System-level design and technology decisions.
- [`docs/planning.md`](docs/planning.md), [`docs/prd.md`](docs/prd.md), [`docs/research.md`](docs/research.md) – Prior planning materials.
- [`tests/`](tests/) – Automated regression tests for the video pipeline.

## Quickstart (Local Python)

1. **Create a virtual environment & install dependencies**
   ```bash
   make install-dev
   ```

2. **Run the API**
   ```bash
   make dev
   ```

3. **Run the worker in a second terminal**
   ```bash
   make worker
   ```

4. **Open the interactive docs** at [http://localhost:8000/docs](http://localhost:8000/docs) and use the `POST /api/v1/videos` endpoint to upload an image (`multipart/form-data`).

5. **Poll the job** with `GET /api/v1/videos/{id}` until `status` becomes `completed`, then call `GET /api/v1/videos/{id}/artifact` to retrieve the video path.

Uploads and generated MP4s are written to `./storage/` by default. Override by setting `APP_STORAGE_DIR` in `.env`.

## Environment Variables

Create a `.env` file (or copy `.env.example`) to customize runtime behaviour:

| Variable | Default | Description |
| --- | --- | --- |
| `APP_DATABASE_URL` | `sqlite:///./data/app.db` | SQLAlchemy connection string. Swap for PostgreSQL in production. |
| `APP_STORAGE_DIR` | `storage` | Root directory for uploads, outputs, and temporary files. |
| `APP_ALLOW_ORIGINS` | `['*']` | CORS whitelist. Provide a JSON-style list of origins for production. |
| `APP_JOB_POLL_INTERVAL` | `2.0` | Worker sleep interval (seconds) between queue polls. |
| `APP_WORKER_BATCH_SIZE` | `1` | Number of jobs fetched per worker tick. Increase to parallelize processing. |

## Running in Docker

```bash
docker compose up --build
```

This starts two containers:

- `api` – serves FastAPI on port `8000`.
- `worker` – continuously processes queued jobs.

Artifacts are stored on the named volume `app-data`. Mount a host directory or cloud volume in production.

## Deployment Notes

- Build the container image: `docker build -t image-to-video-api .`
- Provide a persistent volume for `/data` (contains uploads/outputs and SQLite database).
- Set `APP_DATABASE_URL` to a managed database for multi-instance deployments.
- Expose port `8000` behind a reverse proxy (e.g., Nginx, Traefik) with TLS termination.
- Scale workers horizontally by running additional `python -m app.worker` containers.

## Testing & Quality

- Unit tests: `make test`
- Linting: `make lint`
- Formatting: `make format`

CI should run at least `make lint` and `make test`. Add integration tests that hit the API with sample assets as the product matures.

## API Overview

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Basic liveness probe. |
| `POST` | `/api/v1/videos` | Upload an image and request a video. Returns a job descriptor (status `queued`). |
| `GET` | `/api/v1/videos` | Paginated list of recent jobs. |
| `GET` | `/api/v1/videos/{id}` | Retrieve job status and metadata. |
| `GET` | `/api/v1/videos/{id}/artifact` | Retrieve the absolute filesystem path of the rendered video (once complete). |

Uploaded metadata fields (submitted as `multipart/form-data` alongside the `image` file):

- `prompt` *(optional)* – stored for future prompt-driven effects.
- `duration_seconds` *(float)* – defaults to `5.0`.
- `fps` *(int)* – defaults to `24`.
- `effect` *(string)* – currently only `kenburns` is implemented.
- `seed` *(int)* – reserved for deterministic generators.

## Video Pipeline

The worker uses MoviePy to synthesize a smooth pan/zoom (Ken Burns) over the uploaded image:

1. Load the image via Pillow.
2. Dynamically resize and crop each frame to create motion.
3. Write an MP4 (`libx264`, no audio) to the configured outputs directory.

The implementation lives in [`app/video_pipeline.py`](app/video_pipeline.py). Swap in advanced diffusion or face-animation models as they become available.

## Future Enhancements

- Integrate authentication & rate limiting.
- Persist artifacts to S3/GCS with signed URLs instead of raw filesystem paths.
- Introduce task queue middleware (Celery, Dramatiq, or Temporal) for robust scheduling.
- Add observability hooks (Prometheus metrics, tracing) and feature flags.

## Gotchas

- FFmpeg must be available on the host. The Dockerfile installs it; local Python users should install via package manager (`brew install ffmpeg`, `apt install ffmpeg`).
- SQLite + multi-worker: optimistic locking is disabled on SQLite, so avoid running many workers concurrently without moving to PostgreSQL.
- Large images impact render time. Consider enforcing max resolution or downscaling in `app/video_pipeline.py`.

Refer to [`docs/architecture.md`](docs/architecture.md) for deeper architectural context.

