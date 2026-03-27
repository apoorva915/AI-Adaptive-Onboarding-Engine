"""
Compatibility shim.

The backend app now lives in `backend/src/main.py` (run with `uvicorn src.main:app`).
This file keeps older commands like `uvicorn backend.main:app` working.
"""

from backend.src.main import app  # noqa: F401

