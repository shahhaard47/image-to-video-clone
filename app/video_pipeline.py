from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import numpy as np
from moviepy.editor import VideoClip
from PIL import Image

from .config import settings


class VideoGenerationError(RuntimeError):
    pass


def _load_image(image_path: Path) -> np.ndarray:
    try:
        image = Image.open(image_path).convert("RGB")
    except OSError as exc:
        raise VideoGenerationError(f"Failed to open image: {image_path}") from exc
    return np.array(image)


def _kenburns_frame_generator(image_array: np.ndarray, duration: float) -> Callable[[float], np.ndarray]:
    height, width = image_array.shape[:2]
    start_scale = 1.0
    end_scale = 1.15

    def make_frame(t: float) -> np.ndarray:
        progress = max(0.0, min(1.0, t / duration if duration > 0 else 1.0))
        scale = start_scale + (end_scale - start_scale) * progress
        scaled_width = int(math.ceil(width * scale))
        scaled_height = int(math.ceil(height * scale))
        resized = np.array(Image.fromarray(image_array).resize((scaled_width, scaled_height), Image.LANCZOS))

        max_x = max(scaled_width - width, 0)
        max_y = max(scaled_height - height, 0)
        offset_x = int(max_x * progress)
        offset_y = int(max_y * (1 - progress))

        x_end = offset_x + width
        y_end = offset_y + height
        return resized[offset_y:y_end, offset_x:x_end]

    return make_frame


def render_video(image_path: Path, output_path: Path, duration: float, fps: int) -> Path:
    image_array = _load_image(image_path)
    frame_func = _kenburns_frame_generator(image_array, duration)

    clip = VideoClip(make_frame=frame_func, duration=duration)
    clip = clip.set_fps(fps)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio=False,
            fps=fps,
            preset="medium",
            logger=None,
        )
    finally:
        clip.close()

    return output_path


def generate_video(job) -> Path:
    duration = max(job.duration_seconds, 1)
    fps = max(job.fps, 12)
    input_path = Path(job.input_path)
    output_path = Path(job.output_path or settings.output_dir / f"{job.id}.mp4")

    return render_video(input_path, output_path, duration=duration, fps=fps)

