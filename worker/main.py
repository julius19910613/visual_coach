"""Worker service for async video analysis jobs."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import WORKER_SHARED_SECRET
from src.async_job_processor import process_r2_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Visual Coach Worker", version="1.0.0")


class ProcessJobRequest(BaseModel):
    job_id: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/worker/process")
async def process_job(payload: ProcessJobRequest, x_worker_secret: str | None = Header(default=None)):
    if WORKER_SHARED_SECRET and x_worker_secret != WORKER_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized worker request")
    process_r2_job(payload.job_id)
    return {"ok": True, "job_id": payload.job_id}

