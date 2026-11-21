# Kaayal — Devin CLI + Spec Kit Phase 1 Starter

**Goal:** get an inbound call on an **already-provisioned Sarvam number**, have a hosted Sarvam Voice Agent call a protected FastAPI HTTP tool that sends text to OpenAI Responses API, and hear Kaayal respond in Malayalam or English. **No tourism/operator data, bookings, callbacks, dashboard, database, payments or P2P in Phase 1.**

## Included

- `starter/AGENTS.md` — boundaries for Devin CLI
- `starter/.specify/memory/constitution.md` — Spec Kit constitution
- `starter/specs/001-kaayal-telephony/` — spec, plan, research, tasks, API contract, acceptance
- `starter/devin-prompts/` — review, implementation, live validation, Phase 2 clarification
- `starter/docs/` — owner checklist and research handoff notes
- `CLAUDE_RESEARCH_PROMPT.md` — ask Claude to produce a source-backed `.xlsx` and `.pptx` for **review**, not auto-import into live application
- `scripts/bootstrap.sh` — initialize native Spec Kit structure with Devin CLI integration

## Fastest start

```bash
# In this unzipped directory; requires Python >=3.11, uv, Devin CLI, and a Sarvam account.
uv tool install specify-cli
bash scripts/bootstrap.sh kaayal
cd kaayal
devin
```

Then send Devin the contents of `devin-prompts/00-review.md`. After agreeing on the Sarvam dashboard/manual setup, send `devin-prompts/01-implement-phase1.md`. You may use the official `/speckit-*` commands installed by the CLI integration to reconcile specifications/tasks, but don't let these generate Phase 2 code.

**Critical:** Do not paste Sarvam or OpenAI secrets into Devin prompts or commit them to Git. Set them in local `.env` or protected deployment variables. The user must do final phone-number binding in Sarvam if Devin lacks workspace access.

**Spec Kit bootstrap note:** The command uses `specify init ... --integration devin`. Check `specify init --help` if your locally installed Specify CLI uses a different flag after an upstream update. The bootstrap copies the reviewable handoff docs over generated scaffolding; it will never overwrite an existing target directory.
