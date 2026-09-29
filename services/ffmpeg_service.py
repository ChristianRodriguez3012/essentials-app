from __future__ import annotations

import subprocess
from pathlib import Path


class FFmpegRenderError(RuntimeError):
    pass


def _resolution_value(resolution: str) -> str:
    return "3840:2160" if resolution == "4k" else "1920:1080"


def render_audio_image_video(
    audio_path: Path,
    image_path: Path,
    output_path: Path,
    container: str = "mp4",
    resolution: str = "1080p",
    auto_black_background: bool = False,
) -> Path:
    if container not in {"mp4", "mkv"}:
        raise FFmpegRenderError("Unsupported container format")
    if resolution not in {"1080p", "4k"}:
        raise FFmpegRenderError("Unsupported resolution")
    if any(path.name.startswith("-") for path in (audio_path, image_path, output_path)):
        raise FFmpegRenderError("Invalid path names for ffmpeg inputs")

    size = _resolution_value(resolution)

    if auto_black_background:
        vf = f"scale={size}:force_original_aspect_ratio=decrease,pad={size}:(ow-iw)/2:(oh-ih)/2:black"
    else:
        vf = f"scale={size}:force_original_aspect_ratio=increase,crop={size}"

    command = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio_path),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "slow" if container == "mkv" else "medium",
        "-crf",
        "16" if container == "mkv" else "19",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-shortest",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, shell=False)
    except FileNotFoundError as exc:
        raise FFmpegRenderError("ffmpeg is not installed on the server") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise FFmpegRenderError(stderr or "ffmpeg command failed") from exc

    return output_path
