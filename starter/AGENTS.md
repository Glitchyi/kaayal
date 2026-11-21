# AGENTS.md — Kaayal (കായൽ), Devin CLI guardrails

Read `specs/001-kaayal-telephony/spec.md`, `plan.md`, `tasks.md`, `contracts/openapi.yaml` and `docs/REVIEW_DECISIONS.md` before writing code.

## First-principles scope

- **Phase 1 = inbound phone call → Sarvam-hosted agent → protected FastAPI tool → OpenAI Responses API → spoken reply.** This is the ONLY implementation scope.
- **No databases, customer records, callbacks, operator inventory, fleet onboarding, booking tools, dashboards, WhatsApp, payments, KYC, Aadhaar, website, maps, Iroh, P2P, agent orchestration frameworks, or infrastructure clusters** until owner explicitly opens Phase 2. Do not generate synthetic tourism/operator data.
- Sarvam owns the call and hosted conversation. OpenAI is invoked through an HTTP tool; never misrepresent OpenAI as natively replacing the Sarvam-hosted runtime. Confirm official provider payload/response schemas before implementation.
- Do not provision a new number, trigger unapproved paid services, or place calls without explicit permission. The user already has a Sarvam number.
- Phase 2 is **questions and research only**. Before any Phase 2 implementation, ask the owner the questions in `docs/PHASE2_CLARIFICATIONS.md` and receive approval.

## Security + correctness

- Never expose `OPENAI_API_KEY` or Sarvam credentials in code, browser, logs, or git; `.env.example` only has placeholders.
- The tool endpoint requires authentication, validated payloads, bounded input size, tight timeouts, and a safe fallback on failure.
- Do not log raw phone numbers, full transcripts, API keys, or tool secrets. Use opaque request/interaction IDs for tracing.
- Avoid durable storage for Phase 1. Test with mocked OpenAI calls; record real-call evidence only with the user's authorization.
- Respond in the caller's language where supported, naturally and briefly. Do not invent prices, operators, availability, or successful actions.

## Workflow

1. `00-review.md`: verify platform/API assumptions and request genuinely blocking manual settings.
2. `01-implement-phase1.md`: implement minimal FastAPI app, tests, docs.
3. `02-live-call-verification.md`: validate webhook/tool invocations and live speech, with owner supplying the call.
4. `03-phase2-questions-only.md`: gather choices; do not code Phase 2.

At each milestone report: what worked, actual evidence, what is untested, and the next manual action. No false success reports.
