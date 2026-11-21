# How Sarvam and OpenAI fit together in Kaayal

Two different "agents" are involved — they do very different jobs.

## Who does what

| Component | What it is | What it does |
| --- | --- | --- |
| **Paayal (Sarvam hosted voice agent)** | Sarvam's platform running on your phone number | Answers the call, understands Malayalam/English speech, decides which tool to call, speaks replies. This is the "brain and voice" the caller experiences. |
| **OpenAI Responses API** | A text-generation API called by our backend | Only used inside the `voice_reply` tool — when the caller asks a general open-ended question (about Kaayal, Kerala, travel), Sarvam forwards the question to our endpoint, our backend asks OpenAI to write a short speakable answer, and Sarvam reads it aloud. |
| **Kaayal FastAPI backend** | Our server at `kaayal.glitchy.systems` | Authenticates tool calls, queries the SQLite catalog, stores booking requests, and (only for `voice_reply`) calls OpenAI. |

## The important distinction

- **OpenAI does NOT run the call.** It never hears audio, never sees the phone call, never decides what Paayal does. It only writes short answer text when the `voice_reply` tool is invoked.
- **Sarvam's hosted LLM** (you don't pick it; Sarvam routes it) decides *when* to call tools based on the Paayal prompt. That's why the prompt matters — it's the only control we have over tool usage.
- **Catalog + bookings never touch OpenAI.** `list_boats`, `get_boat`, and `create_booking_request` hit our own database directly and return structured JSON. This is deliberate: listings and requests must come from verified data, not a language model's memory — nothing invented, and every request is auditable.

## Call flow

```
Caller → Sarvam number → Paayal (Sarvam: STT → hosted LLM → TTS)
                          │
                          ├─ tool:voice_reply ──→ FastAPI ──→ OpenAI ──→ text back ──→ spoken
                          │
                          ├─ tool:list_boats ───→ FastAPI ──→ SQLite ──→ JSON ──→ spoken
                          ├─ tool:get_boat ─────→ same
                          └─ tool:create_booking_request ──→ FastAPI ──→ DB row ──→ portal
```

So on a typical call: Paayal greets → general question goes through `voice_reply` (OpenAI writes the answer) → boat question hits `list_boats` (real data) → booking request hits `create_booking_request` (real DB row) → operator confirms by phone.
