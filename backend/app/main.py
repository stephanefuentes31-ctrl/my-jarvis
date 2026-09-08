import json
import logging
import time
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .config import get_settings
from .models import ChatRequest, SpeechRequest
from .services import stream_groq, synthesize_speech

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="JARVIS API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/")
async def dashboard() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/assets/{asset_path:path}")
async def assets(asset_path: str) -> FileResponse:
    return FileResponse(ROOT / "frontend" / "assets" / asset_path)


@app.get("/api/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {"status": "online", "integrations": {"groq": bool(settings.groq_api_key), "fish_audio": bool(settings.fish_audio_api_key and settings.fish_audio_voice_id)}}


@app.post("/api/chat/stream")
async def chat(request: ChatRequest) -> StreamingResponse:
    started = time.perf_counter()

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for delta in stream_groq(request.message, request.history, get_settings()):
                yield json.dumps({"type": "delta", "content": delta}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
        finally:
            logger.info("chat_complete latency_ms=%d history_count=%d", (time.perf_counter() - started) * 1000, len(request.history))

    return StreamingResponse(event_stream(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/speech")
async def speech(request: SpeechRequest) -> StreamingResponse:
    try:
        audio, content_type = await synthesize_speech(request.text, get_settings())
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except httpx.HTTPError as error:
        logger.warning("fish_audio_failed error=%s", type(error).__name__)
        raise HTTPException(status_code=502, detail="Voice playback is unavailable.") from error
    return StreamingResponse(iter([audio]), media_type=content_type)

