# Phase 1 owner quickstart (Devin should fill exact Sarvam UI steps)

## Prerequisites
- Access to the existing Sarvam phone number and Voice Agents dashboard.
- OpenAI API credits and an API key stored safely outside Git.
- Python 3.11+, Devin CLI, local internet access and an HTTPS tunnel tool.

## Steps
1. Open project in Devin and run the review prompt; verify Sarvam dashboard's supported incoming-call integration.
2. Add `OPENAI_API_KEY`, `OPENAI_MODEL`, `SARVAM_TOOL_SHARED_SECRET` to a local `.env` (never commit).
3. Start FastAPI locally as documented by Devin and confirm `GET /health` returns HTTP 200.
4. Expose local port through a secure HTTPS tunnel and verify its public `/health` endpoint.
5. In Sarvam, set the Kaayal agent prompt and register the HTTP tool against `${KAAYAL_PUBLIC_BASE_URL}/api/voice/reply` using official request and response formats; configure shared-secret authentication if supported.
6. Attach the existing phone number to an inbound deployment. Do NOT buy a new number. Owner manually completes privileged dashboard steps.
7. Make a real test call in Malayalam and one in English. Confirm both spoken output and sanitized OpenAI tool invocation evidence.
8. Record actual failure mode and fix the smallest issue; do not add Phase 2 features.

## Failure fallback
If Sarvam tools are not invoking OpenAI, first prove a static HTTP tool response is spoken, then restore the OpenAI call; if the platform cannot support the required response schema, document and ask owner before changing the architecture.
