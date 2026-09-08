import json
import logging
from collections.abc import AsyncIterator

import httpx

from .config import Settings
from .models import Message
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def stream_groq(message: str, history: list[Message], settings: Settings) -> AsyncIterator[str]:
    """Yield Groq response deltas in a transport-neutral form."""
    if not settings.groq_api_key:
        yield "The language model is not configured. Add GROQ_API_KEY to your local environment."
        return

    payload = {
        "model": "llama-3.3-70b-versatile",
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": item.role, "content": item.content} for item in history],
            {"role": "user", "content": message},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:]
                    if raw == "[DONE]":
                        return
                    delta = json.loads(raw).get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        yield delta
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("groq_stream_failed error=%s", type(error).__name__)
        yield "I'm having trouble reaching the language model. Please try again shortly."


async def synthesize_speech(text: str, settings: Settings) -> tuple[bytes, str]:
    """Request audio from Fish Audio without retaining or logging user content."""
    if not settings.fish_audio_api_key or not settings.fish_audio_voice_id:
        raise ValueError("Voice synthesis is not configured.")
    payload = {"text": text, "reference_id": settings.fish_audio_voice_id, "format": "mp3"}
    headers = {"Authorization": f"Bearer {settings.fish_audio_api_key}"}
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post("https://api.fish.audio/v1/tts", json=payload, headers=headers)
        response.raise_for_status()
    return response.content, response.headers.get("content-type", "audio/mpeg")

