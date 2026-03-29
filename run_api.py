#!/usr/bin/env python3
"""Start the Visual Coach FastAPI server."""

import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Start the Visual Coach FastAPI server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    print(f"Starting Visual Coach API server at http://{args.host}:{args.port}")
    print(f"API documentation available at http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
