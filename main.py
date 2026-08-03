"""
Car History Content Agent — FastAPI Backend
============================================
Wraps the Gemini agent loop in a REST API.

Endpoints:
    GET  /health      → {"status": "ok"}
    POST /generate    → {"script": str, "wordCount": int, "filename": str}

Local dev:
    uvicorn main:app --reload --port 8000

Production (Render sets $PORT automatically):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import sys
import os
from pathlib import Path

# ── Force UTF-8 so agent print statements don't crash on Windows ──────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Load .env before importing agent (agent also loads it, but be safe) ────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the refactored run_agent from agent.py
from agent import run_agent

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Car History Content Agent API",
    description="Generates short-form car history video scripts using Gemini + DuckDuckGo.",
    version="1.0.0",
)

# CORS — wildcard so any origin (Lovable preview, published domain, localhost) can call this.
# Render does NOT need any extra CORS config — this is handled entirely in FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response schemas ─────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    topic: str

class ImageItem(BaseModel):
    url:              str
    photographer:     str
    photographer_url: str

class GenerateResponse(BaseModel):
    script:    str
    wordCount: int
    filename:  str
    images:    list[ImageItem] = []

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Quick liveness check."""
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """
    Run the full Gemini agent loop for the given topic.
    The agent will:
      1. web_search for facts
      2. get_car_specs for precise numbers (if needed)
      3. save_script to scripts/<filename>.txt
    Returns the script content, word count, and filename.
    """
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=422, detail="'topic' must be a non-empty string.")

    try:
        result = run_agent(req.topic.strip())
    except ValueError as e:
        # Missing API key or similar config error
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Unexpected agent error
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    if not result.get("script"):
        raise HTTPException(
            status_code=500,
            detail="Agent completed but produced no script. Try again."
        )

    return GenerateResponse(
        script=result["script"],
        wordCount=result["wordCount"],
        filename=result["filename"],
        images=result.get("images", []),
    )


# ── Local / production entrypoint ──────────────────────────────────────────────
# Render injects $PORT dynamically — never hardcode a port number.
# Locally falls back to 8000 if PORT is not set.
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
