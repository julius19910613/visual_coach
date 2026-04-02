"""Async job processing pipeline for R2-based analysis."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import unquote

from config.settings import get_video_mime_type
from src.analyzer import analyze_player_video
from src.gemini_client import GeminiAnalyzerError
from src.job_store import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PROCESSING,
    get_job,
    update_job_status,
)
from src.r2_storage import R2StorageError, download_video_to_temp

logger = logging.getLogger(__name__)


def _guess_suffix(object_key: str) -> str:
    suffix = Path(object_key).suffix.lower()
    return suffix if suffix else ".mp4"


def _normalize_object_key(key: str) -> str:
    """Normalize the object key: URL-decode if it looks percent-encoded."""
    if "%" in key:
        try:
            decoded = unquote(key)
            decoded.encode("utf-8")
            return decoded
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    return key


def process_r2_job(job_id: str) -> None:
    """Process a queued analysis job from R2 object key.

    Strategy: always download from R2 to a temp file, then use the
    Gemini File API or inline data for analysis. This avoids issues
    with presigned URL compatibility (Part.from_uri only supports
    Google Cloud Storage and YouTube URLs, not arbitrary S3/R2 URLs).
    """
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")
    object_key = _normalize_object_key(job.get("r2_object_key") or "")
    if not object_key:
        raise ValueError(f"Job {job_id} missing r2_object_key")

    logger.info("Processing job %s with object_key=%r", job_id, object_key)
    update_job_status(job_id, JOB_STATUS_PROCESSING)
    tmp_path: Path | None = None
    try:
        tmp_path = download_video_to_temp(object_key, suffix=_guess_suffix(object_key))
        logger.info("Downloaded to %s, analyzing...", tmp_path)
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
