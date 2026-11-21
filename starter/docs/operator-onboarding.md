# Adding an operator to Kaayal — owner steps

Takes ~2 minutes. You need your `ADMIN_TOKEN` (from `starter/.env`).

## 1. Create the operator

Open `https://kaayal.glitchy.systems/admin?t=<ADMIN_TOKEN>` → **Add operator** → enter name + phone → submit.

You get a **unique portal link** like `https://kaayal.glitchy.systems/portal/<long-token>`. It's shown once — copy it. That link IS the operator's access; treat it like a password (if lost, create a new operator).

## 2. Share the link

Send it to the operator however you normally talk to them (call, WhatsApp, in person). No login needed — they open the link and see their dashboard.

## 3. Operator adds their boat(s)

On their portal page: **Add a boat** → name, capacity, embarkation point, optional photo URL. Boats show `pending verification` and are invisible to callers.

## 4. You verify the boat

Back in `/admin` → **Boats** table → **Verify**. Now it's live: it appears on the landing page and Paayal can talk about it on calls.

## 5. Requests flow

When a caller leaves a booking request for their boat, it appears on the operator's portal with Confirm/Block. On **Confirm**, the customer's name + number is revealed — the operator calls them back directly.

## If a portal link leaks

There's currently no token reissue — create a new operator record and move their boats, or ask me to add a reissue/deactivate button.
