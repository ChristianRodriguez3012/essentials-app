import os
from pathlib import Path
from typing import Iterable

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _build_youtube_client():
    client_secret_file = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

    if not Path(client_secret_file).exists():
        raise RuntimeError(
            "Missing OAuth client secret file. Set YOUTUBE_CLIENT_SECRET_FILE or place client_secret.json at project root."
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: Iterable[str],
    privacy_status: str,
):
    if not video_path.exists():
        raise RuntimeError("Rendered video does not exist")

    youtube = _build_youtube_client()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": list(tags),
                "categoryId": "10",
            },
            "status": {
                "privacyStatus": privacy_status,
            },
        },
        media_body=MediaFileUpload(str(video_path), resumable=True),
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    return response
