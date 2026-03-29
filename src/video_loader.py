"""Load and validate local video files."""

from pathlib import Path

from config.settings import (
    FILE_API_MAX_BYTES,
    get_video_mime_type,
    INLINE_VIDEO_MAX_BYTES,
)


class VideoLoadError(Exception):
    """Raised when video loading or validation fails."""

    pass


class VideoInfo:
    """Information about a loaded video."""

    def __init__(
        self,
        path: Path,
        bytes_data: bytes,
        mime_type: str,
        size_bytes: int,
        use_inline: bool,
    ):
        self.path = path
        self.bytes_data = bytes_data
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.use_inline = use_inline


def load_video(file_path: str | Path) -> VideoInfo:
    """
    Load and validate a local video file.

    Args:
        file_path: Path to the video file.

    Returns:
        VideoInfo with bytes, mime type, and whether to use inline (vs File API).

    Raises:
        VideoLoadError: If path is invalid, format unsupported, or file too large.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise VideoLoadError(f"File not found: {path}")
    if not path.is_file():
        raise VideoLoadError(f"Not a file: {path}")

    mime_type = get_video_mime_type(path)
    if not mime_type:
        raise VideoLoadError(
            f"Unsupported video format: {path.suffix}. "
            f"Supported: .mp4, .mpeg, .mpg, .mov, .avi, .flv, .webm, .wmv, .3gpp"
        )

    size_bytes = path.stat().st_size
    if size_bytes > FILE_API_MAX_BYTES:
        raise VideoLoadError(
            f"Video too large: {size_bytes / (1024**3):.1f} GB. "
            f"Maximum: {FILE_API_MAX_BYTES / (1024**3):.0f} GB"
        )

    bytes_data = path.read_bytes()
    use_inline = size_bytes < INLINE_VIDEO_MAX_BYTES

    return VideoInfo(
        path=path,
        bytes_data=bytes_data,
        mime_type=mime_type,
        size_bytes=size_bytes,
        use_inline=use_inline,
    )
