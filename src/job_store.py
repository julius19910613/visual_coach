"""SQLite-backed job persistence for async video analysis."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import JOB_STORE_PATH

JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> Path:
    return Path(JOB_STORE_PATH)


def init_job_store() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                job_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                r2_object_key TEXT,
                status TEXT NOT NULL,
                error TEXT,
                result_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_job(source_type: str, r2_object_key: str | None = None) -> dict[str, Any]:
    init_job_store()
    job_id = str(uuid.uuid4())
    now = _now_iso()
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            INSERT INTO analysis_jobs (
                job_id, source_type, r2_object_key, status, error, result_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)
            """,
            (job_id, source_type, r2_object_key, JOB_STATUS_PENDING, now, now),
        )
        conn.commit()
        return {
            "job_id": job_id,
            "source_type": source_type,
            "r2_object_key": r2_object_key,
            "status": JOB_STATUS_PENDING,
            "error": None,
            "result": None,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        conn.close()


def get_job(job_id: str) -> dict[str, Any] | None:
    init_job_store()
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM analysis_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if not row:
            return None
        result = json.loads(row["result_json"]) if row["result_json"] else None
        return {
            "job_id": row["job_id"],
            "source_type": row["source_type"],
            "r2_object_key": row["r2_object_key"],
            "status": row["status"],
            "error": row["error"],
            "result": result,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def update_job_status(job_id: str, status: str, *, error: str | None = None, result: dict[str, Any] | None = None) -> bool:
    init_job_store()
    now = _now_iso()
    conn = sqlite3.connect(_db_path())
    try:
        payload = json.dumps(result, ensure_ascii=False) if result is not None else None
        cur = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = ?, error = ?, result_json = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (status, error, payload, now, job_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

