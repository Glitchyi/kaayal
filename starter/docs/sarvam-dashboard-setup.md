# Sarvam dashboard setup — Paayal voice agent

Configures the Sarvam Voice Agents dashboard for Kaayal. The agent (Paayal)
answers an existing provisioned number and calls six tools on the FastAPI
backend over the public tunnel URL.

## 0. Prerequisites

- Stack running: `cd starter && docker compose up -d` — verify
  `curl http://localhost:8000/health` → `{"status":"ok"}` and
  `curl https://kaayal.glitchy.systems/health` → same.
- The tool secret, used by every tool below:
  `grep SARVAM_TOOL_SHARED_SECRET starter/.env`
- An already-provisioned phone number in the Sarvam dashboard
  (**Deploy → Phone Numbers**). Do not rent or import a new one.

## 1. Store the secret

Dashboard → **Settings → Secrets** → add `KAAYAL_TOOL_TOKEN` with the value
of `SARVAM_TOOL_SHARED_SECRET` from `.env` via the masked input.

> The single most common failure is a stale/missing token here: every tool
> call returns `401` and the agent can only say it "couldn't pull up"
> anything. If tools 401, fix this first — not the prompt.

## 2. Create the six API tools

In the agent builder (**Build**), create six API tools. Shared settings:

- **When should this tool run?** — `run` (during conversation)
- **Auth** — `api_key`, header `X-Kaayal-Tool-Token`, value =
  the `KAAYAL_TOOL_TOKEN` secret
- **Max wait** — 10–15 s
- **On failure** — a short honest line, e.g.
  `Sorry, my service is unreachable right now — can we try again in a moment?`

| Tool | Method | URL |
| --- | --- | --- |
| `voice_reply` | POST | `https://kaayal.glitchy.systems/api/voice/reply` |
| `list_boats` | GET | `https://kaayal.glitchy.systems/api/catalog/boats` |
| `get_boat` | GET | `https://kaayal.glitchy.systems/api/catalog/boats/{boat_id}` |
| `create_booking_request` | POST | `https://kaayal.glitchy.systems/api/voice/request` |
| `create_callback_request` | POST | `https://kaayal.glitchy.systems/api/voice/callback` |
| `caller_context` | POST | `https://kaayal.glitchy.systems/api/voice/caller_context` |

### Request bodies

Use `@` in the body editor to insert variables. `interaction_id` comes from
the call-context picker; the rest are agent variables filled from the
conversation. **Never** map User Identifier or Call Transcript — phone
numbers are collected only through the consented `customer_phone` field.
The one exception is `caller_context`: its `customer_phone` is bound to the
inbound caller-ID variable — it is a read-only lookup key, never stored as
a new customer record.

`voice_reply`:
```json
{
  "utterance": "@caller_question",
  "interaction_id": "@interaction_id",
  "language": "@call_language"
}
```

`list_boats` — add optional query param `q` = caller's keywords
(e.g. "5 people", "shikara").

`create_booking_request`:
```json
{
  "customer_name": "@customer_name",
  "customer_phone": "@customer_phone",
  "consent_given": "@consent_given",
  "boat_id": "@boat_id",
  "preferred_date": "@preferred_date",
  "group_size": "@group_size",
  "notes": "@notes",
  "interaction_id": "@interaction_id"
}
```

`create_callback_request`:
```json
{
  "customer_name": "@customer_name",
  "customer_phone": "@customer_phone",
  "consent_given": "@consent_given",
  "reason": "@callback_reason",
  "boat_id": "@boat_id",
  "keywords": "@keywords",
  "preferred_date": "@preferred_date",
  "interaction_id": "@interaction_id"
}
```

`reason` must be exactly `operator_unreachable` or `no_availability`.

`caller_context`:
```json
{
  "customer_phone": "@caller_id"
}
```
`@caller_id` is the inbound caller's number from call context — do not map
it to a conversational variable. Response: `{known, customer_name,
requests, callbacks}` — `known=false` means a new caller.

### Response templates

- `voice_reply` → `{{reply_text}}` (optionally save `trace_id` into an agent
  variable for debugging)
- `list_boats` → `{{boats}}` — response is `{"boats": [...]}` (wrapped so
  the template has a field to reference); describe each boat's `name`,
  `operator_name`, `capacity`, `embarkation_point`, `price_display`,
  `amenities`, `available`, `operator_reachable`
- `get_boat` → same fields on a single object
- `create_booking_request` → `{{message}}`; statuses `pending`,
  `rejected`, `unavailable`, `unreachable` — the last two mean offer a
  callback
- `create_callback_request` → `{{message}}`; statuses `queued`,
  `opted_out`, `rejected`

## 3. Agent instructions

Paste this whole block into the agent's instructions:

```text
You are Paayal, the voice assistant of Kaayal (കായൽ), connecting callers to
verified boat operators in Alappuzha. Work through the checklist below — do
each item only if needed for the caller's request, and skip steps the caller
has already completed (e.g., if they already gave their name or agreed to
share their number, do not ask again).

[ ] 1. GREET — say you are Paayal, in Malayalam. Continue in the caller's
       language (Malayalam or English). Max two short sentences per turn.

[ ] 2. CLASSIFY the caller's need:
       - Question about Kaayal/Kerala/Alappuzha, boat TYPES, or tourism → step 3
       - Wants OUR listed boats, availability, capacity, prices → step 4
       - Wants to book or leave a request → step 5
       - Says "don't call me" / wants scheduled calls stopped → step 8
       - Anything off-topic → step 10

       Step 3 vs step 4: "what kinds of boats does Alappuzha have?" or
       "tell me about boats" is a general-knowledge question → step 3
       (voice_reply). "What boats do you have right now?" is a catalog
       question → step 4 (list_boats).

[ ] 3. GENERAL ANSWER — call tool:voice_reply, speak the returned text
       naturally. Done → back to step 2 if they ask more.

[ ] 4. BOAT INFO — call tool:list_boats (pass the caller's keywords as q)
       or tool:get_boat for one boat. Speak only what the tool returns:
       name, operator, capacity, embarkation, price_display, amenities,
       available, operator_reachable. If available is false or
       operator_reachable is false → say so and offer step 6. If nothing
       matches, say so and offer step 5. Done → step 2.

[ ] 5. BOOKING REQUEST — collect, skipping anything already given:
       [ ] a. which boat (or "general request" if they don't pick one)
       [ ] b. name
       [ ] c. callback number
       [ ] d. preferred date
       [ ] e. group size
       [ ] f. consent — ask: "I'll share your name and number with the boat
              operator so they can call you back — is that okay?"
       [ ] g. only after a yes: call tool:create_booking_request with
              consent_given=true.
       If the tool returns status "unavailable" or "unreachable" → read the
       message, then go to step 6. If they decline consent: thank them,
       don't save anything. Done → step 2.

[ ] 6. CALLBACK OFFER — when a boat is unavailable or the operator can't be
       reached, offer: "I can call you back when that changes — may I take
       your number for that?" If yes: call tool:create_callback_request with
       consent_given=true and reason "no_availability" or
       "operator_unreachable" (include boat_id when one was discussed).
       Read the returned message. Done → step 2.

[ ] 7. CONFIRM NOTHING — after a request or callback is taken, say only that
       the operator (or Paayal) will call. Never promise booking, price,
       or availability.

[ ] 8. STOP CALLING — if the caller asks not to be called, call
       tool:create_callback_request with their number and
       consent_given=false (this cancels scheduled callbacks), then confirm.

[ ] 9. TOOL FAILURE — if a tool errors or returns an authentication
       failure, say the service is temporarily unavailable and offer to try
       again shortly — never pretend to have boat data you didn't receive.

[ ] 10. OFF-TOPIC — keep a running count of off-topic questions (anything
       not about Kaayal, boats, Alappuzha tourism, or the caller's request).
       Each time, say briefly "I can't help you with that — I'm here for
       Kaayal boat bookings" and offer to return to boats. After the THIRD
       off-topic question, politely say goodbye and end the call.
```

Enable all five tools on the agent (global scope).

## 4. Language and voice

Initial language `ml-IN`, Malayalam-capable voice. The agent may switch to
English when the caller does. Verify actual Malayalam speech on a real call
before claiming support.

## 5. Inbound deployment

1. **Deploy → Inbounds → Create Inbound**
2. **Agent step**: select the Paayal agent + a committed version; attach the
   connection holding the existing number; under **Phone numbers → By
   number**, pick the number.
3. **Availability step**: timezone `Asia/Kolkata`, all days, calls allowed
   `00:00`–`23:59` for testing (default is 09:00–18:00 only).
4. **Review & Deploy** → Deploy.

Editing later requires pausing the deployment; the agent selection is
locked after creation.

## 6. Verify

1. Press **Test** in each tool editor:
   - `voice_reply` → `{reply_text, trace_id}`
   - `list_boats` → JSON array of boats (not `[]` — if empty, seed/verify a
     boat via `/admin` first)
   - `create_booking_request` (consent_given=true) →
     `{request_id, status:"pending", message}`
2. Call the number in Malayalam, then English: ask a general question, ask
   about boats, leave a test request.
3. Server side:
   `docker logs kaayal-app-1 | grep -E "voice_reply|catalog|callback"` —
   expect `200`s, and `voice_reply outcome=ok trace_id=…` lines (sanitized).
4. The test request must appear on the operator's portal and in `/admin`.

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| All tools 401 in app logs | stale/missing dashboard secret | §1 — re-enter `KAAYAL_TOOL_TOKEN` |
| Agent says no boats exist | catalog empty or tool 401 | verify a boat in `/admin`; re-test tool |
| No request/callback in `/admin` | `create_*` call 401'd or never fired | check app logs for the POST; tighten classify step |
| Paayal never calls tools | hosted agent skipped them | tighten step 2 CLASSIFY; confirm tools enabled on agent |
| Calls rejected outside hours | deployment availability window | §5 step 3 — widen to 00:00–23:59 |

Firewall note: if the backend ever sits behind an IP allowlist, permit
Sarvam egress `4.213.167.70` and `35.154.84.150`. Not needed for the tunnel
URL.
