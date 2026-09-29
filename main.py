from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.ffmpeg_service import FFmpegRenderError, render_audio_image_video
from services.youtube_service import YouTubeUploadError, upload_video

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TMP_ROOT = Path(tempfile.gettempdir()) / "essentials"

app = FastAPI(title="ESSENTIALS")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/render-and-upload")
async def render_and_upload(
    audio: UploadFile = File(...),
    image: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    privacy_status: Literal["private", "unlisted", "public"] = Form("private"),
    container: Literal["mp4", "mkv"] = Form("mp4"),
    resolution: Literal["1080p", "4k"] = Form("1080p"),
    auto_black_background: bool = Form(False),
):
    if not audio.filename or not audio.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Audio file must be .wav")

    image_name = (image.filename or "").lower()
    if not image_name.endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Image file must be .png, .jpg, or .jpeg")

    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="job_", dir=TMP_ROOT))

    image_format = "png" if image_name.endswith(".png") else "jpg"

    try:
        audio_bytes = await audio.read()
        image_bytes = await image.read()

        output_path = render_audio_image_video(
            audio_bytes=audio_bytes,
            image_bytes=image_bytes,
            image_format=image_format,
            output_dir=work_dir,
            container=container,
            resolution=resolution,
            auto_black_background=auto_black_background,
        )

        upload_response = upload_video(
            video_path=output_path,
            title=title,
            description=description,
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            privacy_status=privacy_status,
        )

        return {
            "status": "ok",
            "video_id": upload_response.get("id"),
            "youtube_response": upload_response,
        }
    except FFmpegRenderError as exc:
        raise HTTPException(status_code=500, detail=f"Render error: {exc}") from exc
    except YouTubeUploadError as exc:
        raise HTTPException(status_code=500, detail=f"Upload error: {exc}") from exc
    finally:
        audio.file.close()
        image.file.close()
