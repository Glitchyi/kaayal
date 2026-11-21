# Technical plan — Phase 1

## Architecture
`Caller → existing Sarvam number → Sarvam hosted Voice Agent → authenticated HTTPS HTTP tool → FastAPI → OpenAI Responses API → FastAPI response → Sarvam TTS → Caller`

## Stack
Python 3.11+, FastAPI, Pydantic, OpenAI Python SDK, pytest/httpx. Use official Sarvam configuration/dashboard to deploy phone agent. No Svelte or SQLite yet.

## Modules
- `app/main.py`: `GET /health`, `POST /api/voice/reply`.
- `app/openai_adapter.py`: Responses API client, bounded timeout and output length; model env var.
- `app/schemas.py`: Pydantic input/output validation.
- `tests/test_voice_reply.py`: auth, malformed request, timeouts, success, logging redaction using fake OpenAI client.
- `docs/sarvam-dashboard-setup.md`: exact supported config steps and payload/response mapping from current docs.

## HTTP tool integration
Verify current official Sarvam HTTP tool docs before finalizing deployed payload shape; internal contract in `contracts/openapi.yaml` is a proposed adapter and MAY need a mapping layer. Authentication: a high-entropy shared token in a configurable HTTP header, or an official signature mechanism if documented. Reject missing/bad auth. Return sanitized text and trace ID. No call identity required to function.

## OpenAI
Use official Responses API with configurable low-latency text model available to owner; send minimal system instructions and latest caller question with optional bounded context; default no persistence and do not store locally. Model name and token limits must be configurable, not pinned to an account's entitlement.

## Validation
First test `GET /health` locally and through HTTPS tunnel; then unit test OpenAI adapter with mocks; verify Sarvam tool test invocation; lastly make owner-approved real inbound calls. Capture only sanitized evidence (timestamp, correlation ID, success/failure, provider latency), never raw transcript or caller number.
