# Devin CLI prompt — IMPLEMENT Kaayal Phase 1

I approve implementation of **only Phase 1** of Kaayal. Follow `AGENTS.md` and Spec Kit files. First reconcile requirements with official current Sarvam and OpenAI docs; then:
1. Build minimal FastAPI app with `GET /health` and authenticated `POST /api/voice/reply` per OpenAPI contract (mapping payload to Sarvam actual schema if needed).
2. Add server-side OpenAI Responses API adapter with configurable low-latency model, short speakable multilingual replies, timeout handling, and no sensitive transcript logs.
3. Add mocked automated tests for happy path, malformed requests, missing/invalid auth, OpenAI errors/timeouts, and no invented actions.
4. Write `.env.example`, installation/run docs, HTTPS tunnel setup and precise Sarvam dashboard tool/agent/inbound-number setup steps for the *existing number*.
5. Provide an agent prompt that steers substantive questions through `voice_reply` HTTP tool and speaks the exact returned `reply_text` naturally. Verify actual tool invocation with sanitized traces rather than assuming the hosted agent obeys every time.
6. Leave a working self-contained smoke test; do not implement callback queue, operators, booking, UI, DB, or Phase 2.

Report milestone results and what still requires the owner's live-call action. Never buy a number or expose secrets.
