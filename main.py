#!/usr/bin/env python3
"""CLI entry point for player video analysis."""

import argparse
import json
import sys
from pathlib import Path

# Add project root for imports when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.analyzer import analyze_player_video
from src.gemini_client import GeminiAnalyzerError
from src.video_loader import VideoLoadError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze player video using Gemini API. "
        "Outputs structured JSON report with offense/defense dimensions."
    )
    parser.add_argument(
        "video_path",
        type=Path,
        help="Path to local video file (mp4, mov, avi, etc.)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Save report to JSON file (default: print to stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    try:
        report = analyze_player_video(args.video_path)
    except VideoLoadError as e:
        print(f"Video load error: {e}", file=sys.stderr)
        return 1
    except GeminiAnalyzerError as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        return 1

    data = report.model_dump(mode="json")
    json_str = json.dumps(data, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        args.output.write_text(json_str, encoding="utf-8")
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(json_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
