# J.A.R.V.I.S.

A modular, voice-first assistant with a FastAPI streaming backend and a lightweight futuristic web interface.

## Quick start

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open `http://localhost:8000`. Add your credentials only to `.env`; the service reads `GROQ_API_KEY`, `FISH_AUDIO_API_KEY`, and `FISH_AUDIO_VOICE_ID` from the environment.

## API

- `POST /api/chat/stream` streams newline-delimited JSON response chunks.
- `POST /api/speech` synthesizes assistant text using Fish Audio.
- `GET /api/health` reports whether each optional integration is configured without exposing secrets.

The browser uses Web Speech recognition when available and supports typed chat in every browser. Speech synthesis starts after the streamed response completes, keeping the interface responsive while text arrives.

