# Sarvam dashboard setup — Kaayal

Verified against official Sarvam docs on 2026-11-21:

- API/HTTP tool: https://docs.sarvam.ai/voice-agents/build/tools/https-tool
- Tools overview: https://docs.sarvam.ai/voice-agents/build/tools
- Inbound deployments: https://docs.sarvam.ai/voice-agents/deploy/inbounds
- Phone numbers/telephony: https://docs.sarvam.ai/voice-agents/deploy/telephony

## 1. Confirm the existing number

1. Open **Deploy → Phone Numbers** in the Sarvam Voice Agents dashboard.
2. Confirm the already-provisioned number is listed under a connection (rented from Sarvam or imported via Bring Your Own). **Do not buy or rent a new number.**

## 2. Create the API tools

In the agent builder (**Build**), create four **API tools**. All share:

- **When should this tool run?** `run` (During conversation)
- **Auth**: **api_key** → header `X-Kaayal-Tool-Token`, value = `SARVAM_TOOL_SHARED_SECRET`, entered via the **masked secret input** (Settings → Secrets). Never in plain text.
- **Advanced → Max wait**: ~10–15s (max 30s)
- **Advanced → If it fails**: a short honest line, e.g. `Sorry, I'm having trouble reaching my service right now. Could you try again in a moment?`

| Tool | Method | URL | Purpose |
| --- | --- | --- | --- |
| `voice_reply` | POST | `https://kaayal.glitchy.systems/api/voice/reply` | OpenAI-written answers for general questions |
| `list_boats` | GET | `https://kaayal.glitchy.systems/api/catalog/boats` | Verified boats (incl. `available`, `operator_reachable`, `price_display`, `amenities`); optional query `q` |
| `get_boat` | GET | `https://kaayal.glitchy.systems/api/catalog/boats/{boat_id}` | One boat's details; path `boat_id` |
| `create_booking_request` | POST | `https://kaayal.glitchy.systems/api/voice/request` | Store a caller's request after consent; may return `unavailable`/`unreachable` → offer a callback |
| `create_callback_request` | POST | `https://kaayal.glitchy.systems/api/voice/callback` | Queue a consented callback; `consent_given=false` + phone = opt-out |

### Request bodies (use `@` in the body editor to insert variables)

`voice_reply`:
```json
{
  "utterance": "@caller_question",
  "interaction_id": "@interaction_id",
  "language": "@call_language"
}
```

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

- `interaction_id` — pick **Interaction ID** from the call-context variables in the `@` picker.
- Other `@vars` are agent/tool variables the model fills from the conversation; create them in the tool editor if it asks.
- **Do not** map **User Identifier** (caller's number) or **Call Transcript** anywhere — we collect phone numbers only through the consented `customer_phone` field.

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

- `reason` is exactly `operator_unreachable` or `no_availability`.

### Response templates

- `voice_reply` → `{{reply_text}}` (returns `{reply_text, trace_id}`; optionally save `trace_id` into an agent variable for debugging).
- `list_boats` / `get_boat` → describe the returned boats naturally.
- `create_booking_request` → `{{message}}` (returns `{request_id, status, message}`; statuses: `pending`, `rejected`, `unavailable`, `unreachable` — the last two mean offer a callback instead).
- `create_callback_request` → `{{message}}` (statuses: `queued`, `opted_out`, `rejected`).

## 3. Paayal agent prompt (paste into agent instructions)

```text
You are Paayal, the voice assistant of Kaayal (കായൽ), connecting callers to
verified boat operators in Alappuzha. Work through the checklist below — do
each item only if needed for the caller's request, and skip steps the caller
has already completed (e.g., if they already gave their name or agreed to
share their number, do not ask again).

[ ] 1. GREET — say you are Paayal, in Malayalam. Continue in the caller's
       language (Malayalam or English — other Bulbul-supported languages stay out of public claims until tested on real calls). Max two short sentences per turn.

[ ] 2. CLASSIFY the caller's need:
       - General question about Kaayal/Kerala/Alappuzha → step 3
       - Question about boats/operators/capacity/routes → step 4
       - Wants to book or leave a request → step 5
       - Says "don't call me" / wants scheduled calls stopped → step 8
       - Wants a human / something you can't do → step 9

[ ] 3. GENERAL ANSWER — call tool:voice_reply, speak the returned text
       naturally. Done → back to step 2 if they ask more.

[ ] 4. BOAT INFO — call tool:list_boats (pass the caller's keywords as q)
       or tool:get_boat for one boat. Speak only what the tool returns:
       name, operator, capacity, embarkation, price_display, amenities,
       available, operator_reachable. If the boat's available is false or
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

[ ] 9. OUT OF SCOPE / FAILURE — you cannot book, take payments, or call back
       without consent. If a tool errors, say the service is temporarily
       unavailable and offer to try again shortly.
```

Enable all five tools on the agent (global scope).

## 4. Language and voice

Set initial language to Malayalam (`ml-IN`) and pick a Malayalam-capable speaker/voice; the agent can switch to English when the caller does. Verify actual Malayalam speech on a real call before claiming support.

## 5. Create the inbound deployment

1. **Deploy → Inbounds → Create Inbound**.
2. **Agent step**: select the Kaayal agent and a committed version; attach the connection holding your existing number; under **Phone numbers → By number**, pick the existing number.
3. **Availability step**: set timezone `Asia/Kolkata`, all days, and widen **Calls allowed between** to `00:00`–`23:59` for testing (default is 09:00–18:00 only).
4. **Review & Deploy**: tick each section, then **Deploy**.

Editing later requires pausing the deployment first; the agent selection is locked after creation.

## 6. Firewall / IP allowlisting

If you deploy behind a firewall or IP allowlist, permit Sarvam egress IPs `4.213.167.70` and `35.154.84.150`. Not needed for the public tunnel URL.

## 7. Verify

1. Press **Test** in each tool editor — `voice_reply` → `{reply_text, trace_id}`; `list_boats` → JSON array; `create_booking_request` → `{request_id, status:"pending", message}` (test with consent_given=true).
2. Call the number in Malayalam, then English. Ask a general question, a boat question, and leave a test request.
3. Check server logs: `voice_reply outcome=ok trace_id=... interaction_id=...` — sanitized, no transcripts.
4. Confirm the test request appears on the operator's portal and in `/admin`. If Paayal never calls a tool, tighten the classify step — hosted agents don't always invoke tools (documented risk).
