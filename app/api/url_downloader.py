"""URL video downloader for cloud storage services."""

import logging
import re
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class URLDownloadError(Exception):
    """Raised when URL download fails."""
    pass


def extract_google_drive_id(url: str) -> Optional[str]:
    """
    Extract file ID from Google Drive URL.
    
    Supports formats:
    - https://drive.google.com/file/d/{file_id}/view
    - https://drive.google.com/open?id={file_id}
    - https://drive.google.com/uc?id={file_id}
    """
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
        r'/open\?id=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def convert_google_drive_url(url: str) -> str:
    """Convert Google Drive URL to direct download URL."""
    file_id = extract_google_drive_id(url)
    if not file_id:
        raise URLDownloadError(f"Invalid Google Drive URL: {url}")
    
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def convert_dropbox_url(url: str) -> str:
    """Convert Dropbox URL to direct download URL."""
    # Replace www.dropbox.com with dl.dropboxusercontent.com
    # Or change dl=0 to dl=1
    if "dropbox.com" in url:
        if "?dl=0" in url:
            return url.replace("?dl=0", "?dl=1")
        elif "?dl=1" not in url:
            return url + "?dl=1"
    return url


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


async def download_from_url(
    url: str,
    timeout: int = 300,
    max_size: int = 2 * 1024 * 1024 * 1024,  # 2 GB
) -> Path:
    """
    Download video from URL to temporary file.
    
    Args:
        url: Video URL (Google Drive, Dropbox, or direct link)
        timeout: Download timeout in seconds
        max_size: Maximum file size in bytes
    
    Returns:
        Path to downloaded temporary file
    
    Raises:
        URLDownloadError: If download fails
    """
    if not validate_url(url):
        raise URLDownloadError(f"Invalid URL format: {url}")
    
    # Convert cloud storage URLs to direct download URLs
    download_url = url
    if "drive.google.com" in url:
        logger.info("Detected Google Drive URL, converting to direct download")
        download_url = convert_google_drive_url(url)
    elif "dropbox.com" in url:
        logger.info("Detected Dropbox URL, converting to direct download")
        download_url = convert_dropbox_url(url)
    
    logger.info(f"Downloading from: {download_url}")

    # Determine file extension from URL
    parsed_url = urlparse(download_url)
    url_path = Path(parsed_url.path)
    extension = url_path.suffix if url_path.suffix else ".mp4"

    # Create temporary file
    tmp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
    )
    tmp_path = Path(tmp_file.name)
    tmp_file.close()

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Stream download to handle large files
            async with client.stream("GET", download_url) as response:
                # Check response status
                if response.status_code == 404:
                    raise URLDownloadError(f"File not found (404): {url}")
                elif response.status_code == 403:
                    raise URLDownloadError(
                        f"Access denied (403). Make sure the file is publicly accessible: {url}"
                    )
                elif response.status_code >= 400:
                    raise URLDownloadError(
                        f"Download failed with status {response.status_code}: {url}"
                    )

                content_type = response.headers.get("content-type", "")

                # Google Drive virus scan warning: large files show an HTML
                # confirmation page instead of the actual download. Detect it
                # and follow the confirm link.
                if "drive.google.com" in download_url and "text/html" in content_type:
                    logger.info("Google Drive virus scan warning detected, resolving confirm URL")
                    html_body = await _read_full_response(response)
                    confirm_url = _extract_gdrive_confirm_url(html_body, download_url)
                    if not confirm_url:
                        raise URLDownloadError(
                            "Google Drive returned a confirmation page but the "
                            "download link could not be extracted. The file may "
                            "require manual download."
                        )
                    logger.info(f"Resolved confirm URL, retrying download")
                    # Close this response and re-download from the confirm URL
                    return await download_from_url(confirm_url, timeout=timeout, max_size=max_size)

                # Check content length if available
                content_length = response.headers.get("content-length")
                if content_length:
                    file_size = int(content_length)
                    if file_size > max_size:
                        raise URLDownloadError(
                            f"File too large: {file_size / (1024**3):.1f} GB "
                            f"(max: {max_size / (1024**3):.0f} GB)"
                        )
                    logger.info(f"File size: {file_size / (1024**2):.1f} MB")

                # Download in chunks
                downloaded = 0
                chunk_size = 1024 * 1024  # 1 MB chunks

                with open(tmp_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size):
                        downloaded += len(chunk)
                        f.write(chunk)

                        # Check size limit while downloading
                        if downloaded > max_size:
                            raise URLDownloadError(
                                f"File too large: downloaded {downloaded / (1024**3):.1f} GB "
                                f"(max: {max_size / (1024**3):.0f} GB)"
                            )

                logger.info(f"Download completed: {downloaded / (1024**2):.1f} MB")
                return tmp_path

    except httpx.TimeoutException:
        raise URLDownloadError(f"Download timeout after {timeout} seconds: {url}")
    except httpx.RequestError as e:
        raise URLDownloadError(f"Network error: {str(e)}")
    except Exception as e:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise


async def _read_full_response(response: httpx.Response) -> str:
    """Read the full streaming response body as text."""
    chunks: list[bytes] = []
    async for chunk in response.aiter_bytes():
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _extract_gdrive_confirm_url(html: str, original_url: str) -> Optional[str]:
    """
    Extract the confirm/download URL from a Google Drive virus-scan warning page.

    The page typically contains a form with an action URL or a link that
    includes a ``confirm=`` parameter. We look for several known patterns.
    """
    # Pattern 1: <a id="uc-download-link" href="...confirm=...">
    match = re.search(
        r'href="(/uc\?[^"]*confirm=[^"]*)"', html
    )
    if match:
        return f"https://drive.google.com{match.group(1)}"

    # Pattern 2: <form action="...confirm=...">
    match = re.search(
        r'action="(/uc\?[^"]*confirm=[^"]*)"', html
    )
    if match:
        return f"https://drive.google.com{match.group(1)}"

    # Pattern 3: confirm= tacked onto the original URL with a random token
    match = re.search(r'confirm=([a-zA-Z0-9_-]+)', html)
    if match:
        token = match.group(1)
        file_id = extract_google_drive_id(original_url)
        if file_id:
            return (
                f"https://drive.google.com/uc?export=download"
                f"&confirm={token}&id={file_id}"
            )

    return None
