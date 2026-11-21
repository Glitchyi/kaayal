# Handing Claude research to Devin

Run the prompt in `../../CLAUDE_RESEARCH_PROMPT.md` in a Claude environment with browsing and artifact creation. The expected deliverables are `.xlsx`, `.pptx` and `.md`.

**Phase 1:** Devin may read verified provider/documentation findings about Sarvam HTTP tools and OpenAI integration. It must **not** load operator datasets into an application, add database schemas, build listing endpoints, or claim provider inventory exists.

**Phase 2:** Owner reviews and approves each dataset. Devin asks the questions in `PHASE2_CLARIFICATIONS.md`, then maps approved and source-cited rows to a typed data model. Reject unverified operator/pricing/status data, duplicate IDs, or missing source references. Presentation is a communication artifact, not an API/data source.
