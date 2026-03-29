"""Cloudflare R2 storage module for video persistence."""

import logging
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from config.settings import (
    R2_ACCESS_KEY_ID,
    R2_ACCOUNT_ID,
    R2_BUCKET_NAME,
    R2_PUBLIC_URL,
    R2_SECRET_ACCESS_KEY,
)

logger = logging.getLogger(__name__)


class R2StorageError(Exception):
    """Custom exception for R2 storage operations."""


def get_r2_client():
    """Create and return a boto3 client configured for Cloudflare R2."""
    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise R2StorageError(
            "R2 storage is not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
            "and R2_SECRET_ACCESS_KEY environment variables."
        )

    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    logger.debug(f"Creating R2 client for endpoint: {endpoint_url}")

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


def upload_video(file_path: Path, object_key: str) -> str:
    """Upload a video file to R2 and return its public URL.

    Args:
        file_path: Local path to the video file.
        object_key: R2 object key (e.g. "videos/20260329_123456_video.mp4").

    Returns:
        Public URL of the uploaded video.

    Raises:
        R2StorageError: If the upload fails.
    """
    try:
        client = get_r2_client()
        logger.info(f"Uploading {file_path} to R2 as {object_key}")

        client.upload_file(str(file_path), R2_BUCKET_NAME, object_key)

        url = _build_public_url(object_key)
        logger.info(f"Upload complete: {url}")
        return url

    except R2StorageError:
        raise
    except Exception as e:
        raise R2StorageError(f"Failed to upload video to R2: {e}") from e


def generate_presigned_url(object_key: str, expires: int = 3600) -> str:
    """Generate a presigned URL for temporary access to an R2 object.

    Args:
        object_key: R2 object key.
        expires: URL expiration time in seconds (default 1 hour).

    Returns:
        Presigned URL string.

    Raises:
        R2StorageError: If URL generation fails.
    """
    try:
        client = get_r2_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": R2_BUCKET_NAME, "Key": object_key},
            ExpiresIn=expires,
        )
        logger.debug(f"Generated presigned URL for {object_key} (expires in {expires}s)")
        return url

    except R2StorageError:
        raise
    except Exception as e:
        raise R2StorageError(f"Failed to generate presigned URL: {e}") from e


def delete_video(object_key: str) -> bool:
    """Delete a video from R2.

    Args:
        object_key: R2 object key to delete.

    Returns:
        True if deletion succeeded.

    Raises:
        R2StorageError: If deletion fails.
    """
    try:
        client = get_r2_client()
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=object_key)
        logger.info(f"Deleted {object_key} from R2")
        return True

    except R2StorageError:
        raise
    except Exception as e:
        raise R2StorageError(f"Failed to delete video from R2: {e}") from e


def _build_public_url(object_key: str) -> str:
    """Build a public URL for an R2 object.

    Uses R2_PUBLIC_URL if configured (custom domain), otherwise falls back
    to a presigned URL.
    """
    if R2_PUBLIC_URL:
        base = R2_PUBLIC_URL.rstrip("/")
        return f"{base}/{object_key}"
    return generate_presigned_url(object_key)
