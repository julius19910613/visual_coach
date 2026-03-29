"""Gemini API client for video analysis."""

import tempfile
from pathlib import Path

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from src.prompts import SYSTEM_INSTRUCTION, USER_PROMPT
from src.schemas import PlayerAnalysisReport
from src.video_loader import VideoInfo


class GeminiAnalyzerError(Exception):
    """Raised when Gemini API call fails."""

    pass


def analyze_video(video_info: VideoInfo) -> PlayerAnalysisReport:
    """
    Analyze a player video using Gemini and return structured report.

    Args:
        video_info: Loaded video from video_loader.load_video()

    Returns:
        Parsed PlayerAnalysisReport.

    Raises:
        GeminiAnalyzerError: If API key missing or API call fails.
    """
    if not GEMINI_API_KEY:
        raise GeminiAnalyzerError(
            "GEMINI_API_KEY not set. Add it to .env or environment."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    if video_info.use_inline:
        video_part = types.Part(
            inline_data=types.Blob(
                data=video_info.bytes_data,
                mime_type=video_info.mime_type,
            )
        )
    else:
        # File API requires ASCII path; copy to temp file if original path has non-ASCII
        upload_path = video_info.path
        if not all(ord(c) < 128 for c in str(upload_path)):
            ext = Path(video_info.path).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(
                suffix=ext, delete=False
            ) as tmp:
                tmp.write(video_info.bytes_data)
                upload_path = Path(tmp.name)
            try:
                uploaded = client.files.upload(file=str(upload_path))
            finally:
                upload_path.unlink(missing_ok=True)
        else:
            uploaded = client.files.upload(file=str(upload_path))
        video_part = uploaded

    contents: list = [video_part, USER_PROMPT]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_json_schema=PlayerAnalysisReport.model_json_schema(),
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config,
    )

    if not response.text:
        raise GeminiAnalyzerError(
            "Empty response from Gemini. "
            "The model may have blocked the content or returned no text."
        )

    try:
        return PlayerAnalysisReport.model_validate_json(response.text)
    except Exception as e:
        raise GeminiAnalyzerError(
            f"Failed to parse model response as JSON: {e}\nResponse: {response.text}"
        ) from e
