#!/usr/bin/env python3
"""Local test using Ollama instead of Gemini to verify the analysis pipeline."""

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.prompts import SYSTEM_INSTRUCTION, USER_PROMPT
from src.schemas import PlayerAnalysisReport

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:latest"

# Simulated video description for local testing (no actual video needed)
SIMULATED_VIDEO_CONTEXT = """
[模拟视频描述] 这是一段球员比赛集锦视频，时长约3分钟。
画面中球员多次参与进攻：在第02:15完成一次精准直塞助攻，第05:30一脚远射稍稍偏出，
第08:45禁区内射门被门将扑出。防守画面较少，仅在结尾有一两次回追。
"""


def analyze_with_ollama() -> PlayerAnalysisReport:
    """Call local Ollama with structured JSON schema, mimicking the Gemini pipeline."""
    schema = PlayerAnalysisReport.model_json_schema()

    prompt = (
        f"{USER_PROMPT}\n\n"
        f"以下是视频内容描述（本地测试用模拟文本）：\n{SIMULATED_VIDEO_CONTEXT}\n\n"
        f"请严格按照以下 JSON Schema 输出：\n{json.dumps(schema, ensure_ascii=False)}"
    )

    resp = httpx.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"num_predict": 8192},
            "think": False,
            "format": schema,
        },
        timeout=300,
    )
    resp.raise_for_status()

    data = resp.json()
    content = data["message"]["content"]

    if not content:
        raise RuntimeError("Ollama returned empty content (thinking tokens may have used all context)")

    # Strip markdown code block fences if present
    stripped = content.strip()
    if stripped.startswith("```"):
        # Remove opening ```json or ```
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline + 1:]
        # Remove closing ```
        if stripped.endswith("```"):
            stripped = stripped[:-3]
        stripped = stripped.strip()

    return PlayerAnalysisReport.model_validate_json(stripped)


def main() -> int:
    print("Testing local pipeline with Ollama + Qwen3.5...")
    print(f"  Model: {OLLAMA_MODEL}")
    print(f"  Ollama URL: {OLLAMA_URL}")
    print()

    try:
        report = analyze_with_ollama()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    json_str = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)
    print("=== Analysis Report ===")
    print(json_str)

    # Verify structure
    print("\n=== Validation ===")
    print(f"  player_summary: {report.player_summary}")
    print(f"  content_focus: {report.content_focus}")
    print(f"  offense score: {report.dimensions.offense.score}")
    print(f"  offense observability: {report.dimensions.offense.observability}")
    print(f"  defense score: {report.dimensions.defense.score}")
    print(f"  defense observability: {report.dimensions.defense.observability}")
    print(f"  improvements: {len(report.improvements)} items")
    print()
    print("All checks passed! Pipeline is functional.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
