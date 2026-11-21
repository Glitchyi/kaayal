# Research needed before implementation

1. Confirm current Sarvam hosted Voice Agents **HTTP API tool** configuration, request templating and response parsing using official docs; record URL and inspected date.
2. Confirm how an existing number is attached to an inbound deployment and whether answer-hours settings must be 24/7 for testing.
3. Confirm Sarvam voice/language support for Malayalam and English with the selected deployed model; do not infer from other product APIs.
4. Confirm OpenAI official Python Responses API schema and an available economical text model; test without exposing API credentials.
5. Confirm whether outbound HTTP tools allow custom auth headers. If not, propose a safe documented alternative and ask owner before deployment.
6. Confirm public HTTPS tunnel workflow on user's Mac and any webhook verification caveats; only a tool endpoint is required in Phase 1.

Do not invent unavailable provider functions or promise native replacement of Sarvam reasoning. Keep all source links in docs.
