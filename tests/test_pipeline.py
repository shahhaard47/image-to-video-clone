from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.models import VideoJob
from app.video_pipeline import generate_video


def test_generate_video(tmp_path: Path) -> None:
    image_path = tmp_path / "input.png"
    Image.new("RGB", (320, 240), color=(255, 0, 0)).save(image_path)

    output_path = tmp_path / "outputs" / "test.mp4"

    job = VideoJob(
        input_path=str(image_path),
        output_path=str(output_path),
        duration_seconds=1.0,
        fps=12,
    )

    result = generate_video(job)

    assert result.exists()
    assert result.stat().st_size > 0

