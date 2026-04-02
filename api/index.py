"""Vercel serverless entry point — delegates to the full FastAPI app."""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `config`, `src`, `app` are importable.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.api.main import app  # noqa: E402
