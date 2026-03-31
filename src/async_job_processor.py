"""Async job processing pipeline for R2-based analysis."""

from __future__ import annotations

import logging
from pathlib import Path

from config.settings import GEMINI_URL_MAX_BYTES
from src.analyzer import analyze_player_video
from src.gemini_client import GeminiAnalyzerError, analyze_video_from_url
from src.job_store import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PROCESSING,
    get_job,
    update_job_status,
)
from src.r2_storage import (
    R2StorageError,
    download_video_to_temp,
    generate_presigned_url,
    head_video,
)

logger = logging.getLogger(__name__)


def _guess_suffix(object_key: str) -> str:
    suffix = Path(object_key).suffix.lower()
    return suffix if suffix else ".mp4"


def process_r2_job(job_id: str) -> None:
    """Process a queued analysis job from R2 object key."""
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")
    object_key = job.get("r2_object_key")
    if not object_key:
        raise ValueError(f"Job {job_id} missing r2_object_key")

    update_job_status(job_id, JOB_STATUS_PROCESSING)
    tmp_path: Path | None = None
    try:
        meta = head_video(object_key)
        content_length = int(meta.get("ContentLength", 0))
        content_type = meta.get("ContentType") or "video/mp4"

        if content_length > 0 and content_length <= GEMINI_URL_MAX_BYTES:
            signed_url = generate_presigned_url(object_key, expires=900)
            report = analyze_video_from_url(signed_url, mime_type=content_type)
        else:
            tmp_path = download_video_to_temp(object_key, suffix=_guess_suffix(object_key))
            report = analyze_player_video(tmp_path)

        update_job_status(
            job_id,
            JOB_STATUS_COMPLETED,
            result=report.model_dump(mode="json"),
        )
    except (R2StorageError, GeminiAnalyzerError, Exception) as e:
        logger.exception("Job %s failed: %s", job_id, e)
        update_job_status(job_id, JOB_STATUS_FAILED, error=str(e))
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()

