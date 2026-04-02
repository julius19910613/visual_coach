"""FastAPI application for async player video analysis."""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add project root for imports (works for both local and Vercel)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import ASYNC_MODE
from src.job_queue import JobQueueError, enqueue_job
from src.job_store import (
    create_job,
    get_job,
    init_job_store,
)
from src.schemas import PlayerAnalysisReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Visual Coach API",
    description="Async player video analysis API using Google Gemini",
    version="2.0.0",
)


@app.on_event("startup")
async def startup_event():
    init_job_store()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str


class JobCreateResponse(BaseModel):
    """Async job creation response."""

    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Async job status response."""

    job_id: str
    status: str
    error: str | None = None
    result: dict | None = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Visual Coach API",
        "version": "2.0.0",
        "description": "Async player video analysis using Google Gemini API",
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/analyze",
                "description": "Create async analysis job from R2 object key",
            },
            {
                "method": "GET",
                "path": "/api/analyze/{job_id}",
                "description": "Get async analysis job status",
            },
        ],
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="2.0.0")


@app.get("/debug/env")
async def debug_env():
    """Debug: check key environment variables (no secrets)."""
    import os as _os
    return {
        "ASYNC_MODE": _os.getenv("ASYNC_MODE", "(not set)"),
        "R2_ACCOUNT_ID": bool(_os.getenv("R2_ACCOUNT_ID")),
        "R2_BUCKET_NAME": _os.getenv("R2_BUCKET_NAME", "(not set)"),
        "GEMINI_API_KEY": bool(_os.getenv("GEMINI_API_KEY")),
        "VERCEL": _os.getenv("VERCEL", "(not set)"),
    }


@app.post(
    "/api/analyze",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create async analysis job",
    description="Create asynchronous video analysis job from Cloudflare R2 object key.",
    responses={
        202: {
            "description": "Job accepted",
            "model": JobCreateResponse,
        },
        400: {
            "description": "Invalid request",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    },
)
async def analyze_video(
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    r2_object_key: Optional[str] = Form(None),
) -> JobCreateResponse:
    """
    Create analysis job from exactly one source.

    Current async production flow expects `r2_object_key`.
    `file`/`video_url` are accepted for API compatibility but not supported in async mode.
    """
    sources = [file is not None, bool(video_url), bool(r2_object_key)]
    if sum(sources) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide one source: 'file', 'video_url', or 'r2_object_key'.",
        )
    if sum(sources) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one source: 'file', 'video_url', or 'r2_object_key'.",
        )

    if not ASYNC_MODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ASYNC_MODE is disabled. Enable ASYNC_MODE to use async analysis API.",
        )
    if not r2_object_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="In async mode, please provide 'r2_object_key'.",
        )

    # Fix Latin-1 → UTF-8 mojibake from form data encoding on some runtimes (Vercel)
    try:
        r2_object_key = r2_object_key.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass  # already valid UTF-8

    job = create_job(source_type="r2_object_key", r2_object_key=r2_object_key)
    try:
        await enqueue_job(job["job_id"])
    except JobQueueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue analysis job: {e}",
        )

    return JobCreateResponse(job_id=job["job_id"], status=job["status"])


@app.get(
    "/api/analyze/{job_id}",
    response_model=JobStatusResponse,
    summary="Get analysis job status",
)
async def get_analysis_job(job_id: str) -> JobStatusResponse:
    """Get async analysis job status and result."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        error=job["error"],
        result=job["result"],
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
