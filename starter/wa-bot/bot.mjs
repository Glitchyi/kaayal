// Kaayal WhatsApp demo onboarding bot — unofficial open-wa session.
// Pair the 9400354625 phone via the QR this prints on first run, keep it
// running, and inbound DMs get a 3-step onboarding flow ending in a
// one-time operator portal link issued by the Kaayal API.
//
// DEMO ONLY: open-wa automates WhatsApp Web (unofficial, ToS risk).
// Production path is the WhatsApp Business API.

import { create } from "@open-wa/wa-automate";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

// Minimal .env reader so the bot picks up starter/.env without a dep.
function loadEnvFile(path) {
  const out = {};
  try {
    for (const line of readFileSync(path, "utf8").split("\n")) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  } catch {
    /* file optional */
  }
  return out;
}

const env = { ...loadEnvFile(join(here, "..", ".env")), ...process.env };
const API = (env.KAAYAL_API_BASE || "http://localhost:8000").replace(/\/$/, "");
const TOKEN = env.SARVAM_TOOL_SHARED_SECRET;
if (!TOKEN) {
  console.error("SARVAM_TOOL_SHARED_SECRET not found (set it in starter/.env or the environment).");
  process.exit(1);
}

const state = new Map(); // chatId -> { step, name }

async function onboard({ phone, name, boat_name, embarkation }) {
  const res = await fetch(`${API}/api/ops/wa_onboard`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Kaayal-Tool-Token": TOKEN },
    body: JSON.stringify({ phone, name, boat_name, embarkation }),
  });
  if (!res.ok) throw new Error(`onboard failed: HTTP ${res.status}`);
  return res.json();
}

const WELCOME =
  "Namaskaram! Welcome to Kaayal (കായൽ) operator onboarding.\n\n" +
  "Kaayal connects Alappuzha boat operators to callers. Reply with *your name* to start.";

function start(client) {
  console.log("Kaayal wa-bot connected. Waiting for DMs…");
  client.onMessage(async (msg) => {
    try {
      if (msg.fromMe || msg.isGroupMsg || msg.type !== "chat") return;
      const chatId = msg.chatId;
      const phone = (msg.from || chatId).replace(/@.*/, "");
      const text = (msg.body || "").trim();
      if (!text) return;
      const s = state.get(chatId) || { step: 0 };

      if (s.step === 0) {
        await client.sendText(chatId, WELCOME);
        state.set(chatId, { step: 1 });
      } else if (s.step === 1) {
        s.name = text;
        await client.sendText(
          chatId,
          `Thanks ${text}! Now send your boat name and where trips start ` +
            '(e.g. "Shikara Queen, Punnamada") — or reply "skip" if you\'ll add boats later.'
        );
        s.step = 2;
        state.set(chatId, s);
      } else {
        let boat_name = null;
        let embarkation = null;
        if (text.toLowerCase() !== "skip") {
          const [b, e] = text.split(",").map((x) => x.trim());
          boat_name = b || null;
          embarkation = e || null;
        }
        const r = await onboard({ phone, name: s.name, boat_name, embarkation });
        await client.sendText(
          chatId,
          `You're on Kaayal, ${s.name}!\n\n` +
            `Your private portal link (it IS your login — keep it secret):\n${r.portal_url}\n\n` +
            "Open it to add boat details and photos. The Kaayal owner verifies every boat " +
            "before callers hear about it. If the link ever leaks, ask us to re-issue it."
        );
        state.delete(chatId);
      }
    } catch (err) {
      console.error("message handling failed:", err);
      try {
        await client.sendText(msg.chatId, "Sorry, something went wrong on our side — please try again in a moment.");
      } catch {
        /* nothing else we can do */
      }
    }
  });
}

create({ sessionId: "kaayal-demo", multiDevice: true, headless: true, qrTimeout: 0, authTimeout: 0 })
  .then(start)
  .catch((err) => {
    console.error("open-wa failed to start:", err);
    process.exit(1);
  });
