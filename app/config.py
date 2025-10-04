from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration managed via environment variables."""

    database_url: str = "sqlite:///./data/app.db"
    storage_dir: Path = Path("storage")
    upload_subdir: str = "uploads"
    output_subdir: str = "outputs"
    temp_subdir: str = "tmp"
    default_duration_seconds: float = 5.0
    default_fps: int = 24
    job_poll_interval: float = 2.0
    worker_batch_size: int = 1
    allow_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / self.upload_subdir

    @property
    def output_dir(self) -> Path:
        return self.storage_dir / self.output_subdir

    @property
    def temp_dir(self) -> Path:
        return self.storage_dir / self.temp_subdir

    @field_validator("storage_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        return Path(value)


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings behave like a singleton."""

    settings = Settings()
    for path in (settings.storage_dir, settings.upload_dir, settings.output_dir, settings.temp_dir):
        path.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()

