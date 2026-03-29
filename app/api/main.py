"""FastAPI application for player video analysis."""

import logging
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add project root for imports (works for both local and Vercel)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import FILE_API_MAX_BYTES, get_video_mime_type
from src.analyzer import analyze_player_video
from src.gemini_client import GeminiAnalyzerError
from src.schemas import PlayerAnalysisReport
from src.video_loader import VideoLoadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Visual Coach API",
    description="Player video analysis API using Google Gemini - provides structured offense/defense performance reports",
    version="1.0.0",
)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Visual Coach API",
        "version": "1.0.0",
        "description": "Player video analysis using Google Gemini API",
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/analyze",
                "description": "Upload and analyze a player video file",
            },
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check endpoint",
            },
        ],
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post(
    "/api/analyze",
    response_model=PlayerAnalysisReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze player video",
    description="Upload a video file for player performance analysis. Returns structured offense/defense report.",
    responses={
        200: {
            "description": "Successful analysis",
            "model": PlayerAnalysisReport,
        },
        400: {
            "description": "Invalid file format or unsupported video",
            "model": ErrorResponse,
        },
        413: {
            "description": "File too large",
            "model": ErrorResponse,
        },
        500: {
            "description": "Analysis error or internal server error",
            "model": ErrorResponse,
        },
    },
)
async def analyze_video(file: UploadFile = File(...)) -> PlayerAnalysisReport:
    """
    Upload and analyze a player video file.

    Supported formats: .mp4, .mpeg, .mpg, .mov, .avi, .flv, .webm, .wmv, .3gpp
    Maximum file size: 2 GB

    Returns structured analysis with:
    - Player summary
    - Content focus (offensive/defensive/balanced)
    - Offense and defense dimension scores
    - Notable highlights with timestamps
    - Improvement suggestions
    """
    logger.info(f"Received video upload: {file.filename}, content_type: {file.content_type}")

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > FILE_API_MAX_BYTES:
        logger.error(f"File too large: {file_size} bytes (max: {FILE_API_MAX_BYTES})")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size / (1024**3):.1f} GB. Maximum: {FILE_API_MAX_BYTES / (1024**3):.0f} GB",
        )

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    file_path = Path(file.filename)
    mime_type = get_video_mime_type(file_path)

    if not mime_type:
        logger.error(f"Unsupported video format: {file_path.suffix}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format: {file_path.suffix}. "
            f"Supported: .mp4, .mpeg, .mpg, .mov, .avi, .flv, .webm, .wmv, .3gpp",
        )

    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_path.suffix,
        ) as tmp_file:
            # Read and write in chunks to handle large files
            chunk_size = 1024 * 1024  # 1 MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                tmp_file.write(chunk)
            tmp_path = Path(tmp_file.name)
            logger.info(f"Saved uploaded file to temporary location: {tmp_path}")

    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}",
        )

    # Analyze the video
    try:
        logger.info(f"Starting analysis of video: {file.filename}")
        report = analyze_player_video(tmp_path)
        logger.info(f"Analysis completed successfully for: {file.filename}")
        return report

    except VideoLoadError as e:
        logger.error(f"Video load error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video load error: {str(e)}",
        )

    except GeminiAnalyzerError as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}",
        )

    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )

    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()
            logger.info(f"Cleaned up temporary file: {tmp_path}")


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
