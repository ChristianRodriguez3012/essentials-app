from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CLIENT_SECRET = BASE_DIR / "client_secret.json"
DEFAULT_TOKEN_PATH = BASE_DIR / "youtube_token.json"


class YouTubeUploadError(RuntimeError):
    pass


def _get_credentials() -> Credentials:
    token_path = Path(os.getenv("YOUTUBE_TOKEN_PATH", DEFAULT_TOKEN_PATH))
    client_secret_path = Path(os.getenv("YOUTUBE_CLIENT_SECRET", DEFAULT_CLIENT_SECRET))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret_path.exists():
                raise YouTubeUploadError(
                    "Missing OAuth client secret file. Set YOUTUBE_CLIENT_SECRET or add client_secret.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: Sequence[str],
    privacy_status: str,
):
    try:
        credentials = _get_credentials()
        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": list(tags),
                    "categoryId": "10",
                },
                "status": {"privacyStatus": privacy_status},
            },
            media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
        )

        response = None
        while response is None:
            _, response = request.next_chunk()

        return response
    except YouTubeUploadError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise YouTubeUploadError(str(exc)) from exc
