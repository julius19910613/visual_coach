#!/usr/bin/env python3
"""
Upload only team videos (白队 / 黑队) to Cloudflare R2.

Behavior:
- Recursively scan the following directories under project root:
  - 白队
  - 黑队
- Upload all matching video files to the configured R2 bucket.
- Object keys are prefixed with R2_KEY_PREFIX (default: "videos").
- Existing objects with the same key are overwritten.

Configuration (environment variables):
- R2_ACCOUNT_ID          (required)
- R2_ACCESS_KEY_ID       (required)
- R2_SECRET_ACCESS_KEY   (required)
- R2_BUCKET_NAME         (required)
- R2_KEY_PREFIX          (optional, default: "videos")

Usage examples (from project root):
  uv run python scripts/upload_teams_to_r2.py
  uv run python scripts/upload_teams_to_r2.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Ensure script can read project .env when run via uv/python.
load_dotenv(PROJECT_ROOT / ".env", override=True)

TEAM_DIRS = ["白队", "黑队"]

VIDEO_EXTS = {
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
    ".mkv",
    ".mpeg",
    ".mpg",
    ".flv",
    ".wmv",
    ".3gpp",
}


@dataclass
class R2Config:
    account_id: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    key_prefix: str = "videos"

    @property
    def endpoint_url(self) -> str:
        return f"https://{self.account_id}.r2.cloudflarestorage.com"


def load_r2_config() -> R2Config:
    def _req(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise SystemExit(f"Missing required environment variable: {name}")
        return value

    return R2Config(
        account_id=_req("R2_ACCOUNT_ID"),
        access_key_id=_req("R2_ACCESS_KEY_ID"),
        secret_access_key=_req("R2_SECRET_ACCESS_KEY"),
        bucket_name=_req("R2_BUCKET_NAME"),
        key_prefix=os.getenv("R2_KEY_PREFIX", "videos").strip() or "videos",
    )


def create_s3_client(cfg: R2Config):
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        region_name="auto",
    )


def iter_team_videos(root: Path) -> Iterable[Path]:
    for team in TEAM_DIRS:
        base = root / team
        if not base.exists():
            continue
        for ext in VIDEO_EXTS:
            yield from base.rglob(f"*{ext}")


def make_r2_key(cfg: R2Config, file_path: Path) -> str:
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    return f"{cfg.key_prefix}/{rel}"


def upload_file(s3, cfg: R2Config, file_path: Path, key: str, dry_run: bool = False) -> None:
    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"  -> {key}  ({size_mb:.1f} MB)")
    if dry_run:
        return
    s3.upload_file(str(file_path), cfg.bucket_name, key)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upload 白队 / 黑队 视频到 Cloudflare R2（覆盖同名对象，key 前缀默认为 videos/）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将上传的对象 key，不真正上传",
    )
    args = parser.parse_args(argv)

    try:
        cfg = load_r2_config()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Team dirs    : {', '.join(TEAM_DIRS)}")
    print(f"R2 bucket    : {cfg.bucket_name}")
    print(f"Endpoint URL : {cfg.endpoint_url}")
    print(f"Key prefix   : {cfg.key_prefix}")
    print(f"Mode         : {'DRY-RUN' if args.dry_run else 'UPLOAD'}")
    print("")

    videos = sorted(set(iter_team_videos(PROJECT_ROOT)))
    if not videos:
        print("No videos found under 白队 / 黑队")
        return 1

    print(f"Found {len(videos)} video files under 白队 / 黑队\n")

    if not args.dry_run:
        try:
            s3 = create_s3_client(cfg)
            s3.head_bucket(Bucket=cfg.bucket_name)
        except (BotoCoreError, ClientError) as e:
            print(f"Cannot access R2 bucket '{cfg.bucket_name}': {e}", file=sys.stderr)
            return 1
    else:
        s3 = None  # type: ignore[assignment]

    uploaded = 0
    failed = 0

    for idx, file_path in enumerate(videos, start=1):
        key = make_r2_key(cfg, file_path)
        print(f"[{idx}/{len(videos)}] Uploading {file_path.relative_to(PROJECT_ROOT)}")
        try:
            upload_file(s3, cfg, file_path, key, dry_run=args.dry_run)
            uploaded += 1
        except (BotoCoreError, ClientError, OSError) as e:
            failed += 1
            print(f"  !! Failed: {e}", file=sys.stderr)

    print("\nSummary:")
    print(f"  Uploaded (or would upload in dry-run): {uploaded}")
    print(f"  Failed:   {failed}")
    print(f"  Total:    {len(videos)}")

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

