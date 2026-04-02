"""Configuration settings for the player video analyzer."""

import os
from pathlib import Path

from dotenv import load_dotenv

# override=True: project `.env` wins over stale GEMINI_API_KEY in the shell
load_dotenv(override=True)

# Gemini API (strip avoids trailing newline/space from editors)
GEMINI_API_KEY: str = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL_MODEL: str = os.getenv("GEMINI_URL_MODEL", "gemini-3-flash-preview")
GEMINI_URL_MAX_BYTES: int = int(os.getenv("GEMINI_URL_MAX_BYTES", str(100 * 1024 * 1024)))

# Cloudflare R2 Storage (optional — video persistence)
R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "visual-coach-videos")
R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")
R2_ENABLED: bool = bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY)

# Async analysis (Vercel API + worker)
ASYNC_MODE: bool = os.getenv("ASYNC_MODE", "true").strip().lower() == "true"
# Vercel serverless: filesystem is read-only except /tmp
_default_job_store = "/tmp/jobs.db" if os.getenv("VERCEL") else "data/jobs.db"
JOB_STORE_PATH: str = os.getenv("JOB_STORE_PATH", _default_job_store)
WORKER_ENDPOINT: str = os.getenv("WORKER_ENDPOINT", "")
WORKER_SHARED_SECRET: str = os.getenv("WORKER_SHARED_SECRET", "")

# Video size thresholds (bytes)
INLINE_VIDEO_MAX_BYTES: int = 100 * 1024 * 1024  # 100 MB
FILE_API_MAX_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB (free tier)

# Supported video MIME types
SUPPORTED_VIDEO_MIME_TYPES: frozenset[str] = frozenset({
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
})

# Video extensions to MIME mapping
VIDEO_EXTENSION_MIME: dict[str, str] = {
    ".mp4": "video/mp4",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
    ".mov": "video/quicktime",
    ".avi": "video/avi",
    ".flv": "video/x-flv",
    ".webm": "video/webm",
    ".wmv": "video/wmv",
    ".3gpp": "video/3gpp",
}


def get_video_mime_type(file_path: str | Path) -> str | None:
    """Get MIME type for a video file based on extension."""
    ext = Path(file_path).suffix.lower()
    return VIDEO_EXTENSION_MIME.get(ext)
