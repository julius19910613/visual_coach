#!/usr/bin/env python3
"""Start async worker service."""

import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start Visual Coach worker service")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("worker.main:app", host=args.host, port=args.port, reload=args.reload)

