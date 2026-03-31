"""Queue dispatch helpers for async analysis jobs."""

from __future__ import annotations

import logging

import httpx

from config.settings import WORKER_ENDPOINT, WORKER_SHARED_SECRET
from src.async_job_processor import process_r2_job

logger = logging.getLogger(__name__)


class JobQueueError(Exception):
    """Raised when queue dispatch fails."""


async def enqueue_job(job_id: str) -> None:
    """
    Enqueue job for processing.

    If WORKER_ENDPOINT is configured, dispatch to remote worker.
    Otherwise process inline as fallback (useful for local/dev).
    """
    if not WORKER_ENDPOINT:
        process_r2_job(job_id)
        return

    headers = {}
    if WORKER_SHARED_SECRET:
        headers["x-worker-secret"] = WORKER_SHARED_SECRET

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                WORKER_ENDPOINT.rstrip("/") + "/worker/process",
                json={"job_id": job_id},
                headers=headers,
            )
            response.raise_for_status()
    except Exception as e:
        logger.error("Failed to dispatch job %s to worker: %s", job_id, e)
        raise JobQueueError(str(e)) from e

