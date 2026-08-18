"""Compatibility entry point. The FastAPI backend now lives in backend/app.py."""

import uvicorn

from backend.app import app


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)
