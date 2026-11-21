# WhatsApp demo onboarding (open-wa)

**Demo only.** This uses [`@open-wa/wa-automate`](https://github.com/open-wa/wa-automate-nodejs), which automates WhatsApp Web — the *unofficial* API. It can get a number temporarily banned and the session dies if the paired phone goes offline. Production = WhatsApp Business API (separate task).

## How it works

```
Operator DMs +91 9400354625
  → open-wa bot (wa-bot/bot.mjs, running on this machine)
  → "welcome" → asks name → asks boat name + embarkation
  → POST /api/ops/wa_onboard  (tool-token auth, same secret as Sarvam tools)
  → creates/rotates Operator → returns one-time portal URL
  → bot replies in the same chat with the portal link
```

Repeat DM from the same number re-issues the link (old one dies instantly) — that IS the token-reissue flow, no extra commands needed. Boats the operator names in chat land `unverified` (`source="wa-demo"`) — invisible publicly until verified in `/admin`.

## Run it

```bash
cd starter/wa-bot
npm install          # first time only — pulls a Chromium runtime
npm start            # prints a QR code on first run
```

1. On the **9400354625 phone**: WhatsApp → Settings → Linked Devices → Link a Device → scan the QR.
2. Keep `npm start` running (and the phone online) for as long as the demo needs to respond.
3. From any other phone, DM `+91 9400354625` → follow the prompts.

The bot reads `SARVAM_TOOL_SHARED_SECRET` and `KAAYAL_API_BASE` (default `http://localhost:8000`) from `starter/.env`. For the public hostname in portal links, `KAAYAL_PUBLIC_BASE_URL=https://kaayal.glitchy.systems` is already set there.

## Boundaries

- The bot creates *pending operators + unverified boat rows* — operators get `pending verification` until approved in `/admin`, and nothing is publicly listed until verified.
- Raw portal tokens never touch the DB (only SHA-256 hashes) and are never logged.
- Kaayal still sends no messages on the operator's behalf — the bot replies as *the Kaayal number* to onboarding DMs only; customer contact stays manual (portal wa.me links).
- The same onboarding works **without WhatsApp** at `/join` on the website — the bot is a demo convenience, not the only path.

## Migration path → official WhatsApp Business Platform

When ready for production, replace `wa-bot/` with a webhook consumer; the Kaayal-side contract (`POST /api/ops/wa_onboard`) stays identical:

1. Meta developer account → create app → add **WhatsApp** product → register + verify the 9400354625 number (or a dedicated business number — migrating the same SIM requires removing it from consumer WhatsApp).
2. Point the app's webhook at a new `POST /api/wa/webhook` endpoint on this FastAPI service (verify token + app-secret signature check).
3. Map inbound text payloads to the same onboarding state machine (port the step logic from `wa-bot/bot.mjs`).
4. Reply via `POST https://graph.facebook.com/v{ver}/{phone_number_id}/messages` with a permanent access token stored as an env secret — never in code.
5. Note: free-form replies are only allowed inside the 24h customer-service window; beyond that, Meta-approved *message templates* are required. Design the flow so the portal link goes out within the window.

Until then, open-wa is acceptable for demos on a spare number.
