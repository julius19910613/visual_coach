"""Pydantic schemas for structured output from Gemini."""

from typing import Literal

from pydantic import BaseModel, Field


class Highlight(BaseModel):
    """A timestamped highlight from the video."""

    timestamp: str = Field(description="Time in MM:SS format")
    description: str = Field(description="What happened at this moment")


class DimensionResult(BaseModel):
    """Analysis result for offense or defense dimension."""

    score: int | None = Field(
        default=None,
        description="Score 1-5 if enough footage; null when observability is none or partial with insufficient data",
    )
    observability: Literal["full", "partial", "none"] = Field(
        description="full=enough footage to score; partial=some footage but limited; none=no relevant footage"
    )
    notes: str = Field(description="Analysis notes for this dimension")
    highlights: list[Highlight] = Field(
        default_factory=list,
        description="Notable moments with timestamps (only when observability is full or partial)",
    )


class Dimensions(BaseModel):
    """Offense and defense dimension results."""

    offense: DimensionResult = Field(description="Offensive play analysis")
    defense: DimensionResult = Field(description="Defensive play analysis")


class PlayerAnalysisReport(BaseModel):
    """Structured report from player video analysis."""

    player_summary: str = Field(
        description="One-sentence overall evaluation of the player's performance"
    )
    content_focus: Literal["offensive", "defensive", "balanced"] = Field(
        description="Whether the video is mainly offensive, defensive, or balanced"
    )
    dimensions: Dimensions = Field(
        description="Offense and defense dimension analysis"
    )
    improvements: list[str] = Field(
        default_factory=list,
        description="Actionable improvement suggestions"
    )
