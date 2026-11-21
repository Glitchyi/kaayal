# Run locally + expose via HTTPS tunnel — Phase 1

## Setup

```bash
cd starter   # this directory (contains pyproject.toml)
uv sync      # installs Python 3.11 + deps into .venv
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, SARVAM_TOOL_SHARED_SECRET (generate a long random one)
```

Generate a high-entropy shared secret:

```bash
openssl rand -hex 32
```

## Run

```bash
uv run python -m app.main        # serves on $PORT (default 8000)
```

Check:

```bash
curl -s http://localhost:8000/health   # {"status":"ok"}
```

## Tests

```bash
uv run pytest          # mocked OpenAI; no real API key needed
```

## HTTPS tunnel (pick one)

Sarvam API tools require a public HTTPS URL.

- **cloudflared** (free, no signup): `cloudflared tunnel --url http://localhost:8000`
- **ngrok**: `ngrok http 8000`
- **Tailscale Funnel** or any static-URL tunnel also works.

Set `KAAYAL_PUBLIC_BASE_URL` in `.env` to the tunnel's public base URL, and use the same base when registering the tool URL in Sarvam. Tunnel URLs change on restart unless you reserve a named tunnel — recheck `/health` publicly after any restart and update the tool URL in Sarvam if it changed.

## Smoke test (no Sarvam needed)

```bash
bash scripts/smoke.sh http://localhost:8000 "$SARVAM_TOOL_SHARED_SECRET"
```

It verifies `/health`, auth rejection (401), and the reply endpoint. Without a real `OPENAI_API_KEY` the reply call returns an honest `502 upstream_unavailable`; with a key it returns `{reply_text, trace_id}`.
