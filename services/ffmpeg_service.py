import subprocess
from pathlib import Path


RESOLUTION_MAP = {
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
}


def render_video_from_audio_and_image(
    audio_path: Path,
    image_path: Path,
    output_path: Path,
    resolution: str,
    auto_black_bg: bool,
) -> None:
    if resolution not in RESOLUTION_MAP:
        raise RuntimeError(f"Unsupported resolution: {resolution}")

    width, height = RESOLUTION_MAP[resolution]
    fit_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"

    if auto_black_bg:
        vf = (
            f"{fit_filter},"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    else:
        vf = f"scale={width}:{height}"

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
        "medium",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(output_path),
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "Unknown ffmpeg error")
