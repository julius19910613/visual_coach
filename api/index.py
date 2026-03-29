#!/usr/bin/env python3
"""API entry point for Vercel deployment."""

import sys
from pathlib import Path

# Add project root for imports (api/ is at root level)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.main import app

# For Vercel serverless functions
handler = app
