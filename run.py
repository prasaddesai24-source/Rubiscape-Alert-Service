"""
Rubiscape Alert Service — Windows-compatible startup script.

Fixes asyncio event loop policy for uvicorn on Windows (Python 3.10+).
Run this instead of uvicorn directly:
    venv\Scripts\python run.py
"""

import asyncio
import sys

# ── Windows asyncio fix ──────────────────────────────────────
# Python 3.10+ on Windows defaults to ProactorEventLoop which
# causes issues with uvicorn. This sets the correct policy.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning",
    )
