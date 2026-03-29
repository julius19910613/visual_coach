"""Main analysis workflow for player video."""

from pathlib import Path

from src.gemini_client import analyze_video as _analyze_video
from src.gemini_client import GeminiAnalyzerError
from src.schemas import PlayerAnalysisReport
from src.video_loader import VideoLoadError, load_video


def analyze_player_video(file_path: str | Path) -> PlayerAnalysisReport:
    """
    Load a local video and analyze player performance.

    Args:
        file_path: Path to the video file.

    Returns:
        Structured PlayerAnalysisReport with offense/defense dimensions.

    Raises:
        VideoLoadError: If file is invalid or unsupported.
        GeminiAnalyzerError: If API call or parsing fails.
    """
    video_info = load_video(file_path)
    return _analyze_video(video_info)
