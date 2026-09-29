from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.ffmpeg_service import render_video_from_audio_and_image
from services.youtube_service import upload_video

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="ESSENTIALS")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/render-and-upload")
async def render_and_upload(
    audio: UploadFile = File(...),
    image: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    visibility: str = Form("private"),
    container: str = Form("mp4"),
    resolution: str = Form("1080p"),
    auto_black_bg: bool = Form(False),
    mock_upload: Optional[bool] = Form(False),
):
    if not audio.filename or not audio.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Audio file must be a .wav")

    if not image.filename or not image.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Image file must be .png, .jpg, or .jpeg")

    if visibility not in {"private", "unlisted", "public"}:
        raise HTTPException(status_code=400, detail="Visibility must be private, unlisted, or public")

    if container not in {"mp4", "mkv"}:
        raise HTTPException(status_code=400, detail="Container must be mp4 or mkv")

    if resolution not in {"1080p", "4k"}:
        raise HTTPException(status_code=400, detail="Resolution must be 1080p or 4k")

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audio_path = temp_path / audio.filename
        image_path = temp_path / image.filename
        output_ext = "mp4" if container == "mp4" else "mkv"
        output_path = temp_path / f"rendered.{output_ext}"

        audio_path.write_bytes(await audio.read())
        image_path.write_bytes(await image.read())

        try:
            render_video_from_audio_and_image(
                audio_path=audio_path,
                image_path=image_path,
                output_path=output_path,
                resolution=resolution,
                auto_black_bg=auto_black_bg,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=f"FFmpeg render failed: {exc}") from exc

        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if mock_upload:
            return {
                "status": "ok",
                "video_id": "mock-video-id",
                "title": title,
                "visibility": visibility,
                "tags": tag_list,
            }

        try:
            upload_result = upload_video(
                video_path=output_path,
                title=title,
                description=description,
                tags=tag_list,
                privacy_status=visibility,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "video_id": upload_result.get("id")}
