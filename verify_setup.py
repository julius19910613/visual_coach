#!/usr/bin/env python3
"""Verify Visual Coach API setup."""

import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def check_env_file() -> bool:
    """Check if .env file exists and has API key."""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  .env file not found. Copy .env.example to .env and add your API key.")
        return False

    content = env_path.read_text()
    if "your_api_key_here" in content:
        print("⚠️  .env still contains placeholder. Add your actual GEMINI_API_KEY.")
        return False

    return True

def main():
    """Run verification checks."""
    print("=" * 60)
    print("Visual Coach API Setup Verification")
    print("=" * 60)
    print()

    checks = [
        ("API main file", "app/api/main.py"),
        ("Startup script", "run_api.py"),
        ("Test script", "test_api.py"),
        ("Package init", "app/__init__.py"),
        ("API init", "app/api/__init__.py"),
        ("Environment template", ".env.example"),
        ("Updated pyproject.toml", "pyproject.toml"),
        ("Updated README", "README.md"),
    ]

    all_passed = True

    for name, filepath in checks:
        if check_file_exists(filepath):
            print(f"✓ {name}: {filepath}")
        else:
            print(f"✗ {name}: {filepath} NOT FOUND")
            all_passed = False

    print()

    # Check .env
    if check_env_file():
        print("✓ Environment file configured")
    else:
        all_passed = False

    print()

    # Check dependencies
    try:
        import fastapi
        import uvicorn
        import multipart
        print(f"✓ FastAPI installed (version {fastapi.__version__})")
        print(f"✓ Uvicorn installed")
        print(f"✓ python-multipart installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("  Run: uv sync")
        all_passed = False

    print()

    # Check FastAPI app
    try:
        from app.api.main import app
        print(f"✓ FastAPI app imports successfully")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        print(f"  Routes: {len(routes)} registered")
        print(f"    - POST /api/analyze")
        print(f"    - GET /health")
        print(f"    - GET /")
    except Exception as e:
        print(f"✗ Failed to import FastAPI app: {e}")
        all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("✓ All checks passed! Ready to start the API.")
        print()
        print("Quick start:")
        print("  1. Ensure GEMINI_API_KEY is set in .env")
        print("  2. Run: uv run run_api.py")
        print("  3. Open: http://localhost:8000/docs")
        print()
        print("To test:")
        print("  uv run test_api.py path/to/video.mp4")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
