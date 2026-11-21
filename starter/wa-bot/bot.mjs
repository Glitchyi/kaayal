// Kaayal WhatsApp demo onboarding bot — unofficial open-wa session.
// Pair the 9400354625 phone via the QR this prints on first run, keep it
// running, and inbound DMs get a 3-step onboarding flow ending in a
// one-time operator portal link issued by the Kaayal API.
//
// DEMO ONLY: open-wa automates WhatsApp Web (unofficial, ToS risk).
// Production path is the WhatsApp Business API.

import { create } from "@open-wa/wa-automate";
import { readFileSync, unlinkSync } from "node:fs";
import { createServer } from "node:http";
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

// Repeat-DM fast path: 404 = unknown number → run the onboarding flow.
async function reissue(phone) {
  const res = await fetch(`${API}/api/ops/wa_reissue`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Kaayal-Tool-Token": TOKEN },
    body: JSON.stringify({ phone }),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`reissue failed: HTTP ${res.status}`);
  return res.json();
}

const WELCOME =
  "Namaskaram! Welcome to Kaayal (കായൽ) operator onboarding.\n\n" +
  "Kaayal connects Alappuzha boat operators to callers. Reply with *your name* to start.";

function start(client) {
  console.log("Kaayal wa-bot connected. Waiting for DMs…");
  client.onStateChanged((s) => {
    console.log(`wa-bot state: ${s}`);
    // Unrecoverable states need a re-pair; exit so the supervisor (restart
    // policy / launchd) respawns us and prints a fresh QR instead of
    // sitting alive-but-dead.
    if (["CONFLICT", "UNPAIRED", "UNPAIRED_IDLE"].includes(s)) {
      console.error("session unpaired/conflicted — exiting for restart");
      process.exit(1);
    }
  });
  client.onMessage(async (msg) => {
    try {
      // Log shape only — never the raw phone number or body (PII rules).
      console.log(
        `inbound msg: type=${msg.type} group=${!!msg.isGroupMsg} fromMe=${!!msg.fromMe} from=…${String(msg.from || msg.chatId || "").replace(/@.*/, "").slice(-4)}`
      );
      if (msg.fromMe || msg.isGroupMsg || msg.type !== "chat") return;
      const chatId = msg.chatId;
      const phone = (msg.from || chatId).replace(/@.*/, "");
      const text = (msg.body || "").trim();
      if (!text) return;
      const s = state.get(chatId) || { step: 0 };

      if (s.step === 0) {
        const known = await reissue(phone);
        if (known) {
          await client.sendText(
            chatId,
            known.portal_url
              ? `Welcome back, ${known.name}!\n\n` +
                  `Fresh portal link (the old one just died):\n${known.portal_url}`
              : `You're already registered, ${known.name} — still *pending verification*. ` +
                  "We'll WhatsApp you the portal link once the owner approves."
          );
        } else {
          await client.sendText(chatId, WELCOME);
          state.set(chatId, { step: 1 });
        }
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
          r.portal_url
            ? `You're on Kaayal, ${s.name}!\n\n` +
                `Your private portal link (it IS your login — keep it secret):\n${r.portal_url}\n\n` +
                "Open it to add boat details and photos. The Kaayal owner verifies every boat " +
                "before callers hear about it. If the link ever leaks, ask us to re-issue it."
            : `Thanks ${s.name} — you're registered with Kaayal, status: *pending verification*. ` +
                "The owner will review your details and we'll send your portal link here once approved."
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
  // Diagnostic: fires for every message event, not just inbound chats.
  client.onAnyMessage((msg) => {
    console.log(
      `any-msg: type=${msg.type} group=${!!msg.isGroupMsg} fromMe=${!!msg.fromMe}`
    );
  });
  // Push channel for the app: POST /send {phone, text} authed with the shared
  // tool token — delivers messages without an inbound DM (e.g. portal link
  // on operator approval). Internal network only, never published.
  createServer((req, res) => {
    if (req.method !== "POST" || req.url !== "/send") {
      res.writeHead(404).end();
      return;
    }
    if (req.headers["x-kaayal-tool-token"] !== TOKEN) {
      res.writeHead(401).end();
      return;
    }
    let body = "";
    req.on("data", (c) => {
      body += c;
      if (body.length > 4096) req.destroy();
    });
    req.on("end", async () => {
      try {
        const { phone, text } = JSON.parse(body);
        const digits = String(phone || "").replace(/\D/g, "");
        if (!digits || !text) throw new Error("bad payload");
        // Free tier can't start new chats — reuse an existing one when the
        // number has DM'd the bot before (onboarded operators always have).
        const chats = (await client.getAllChats().catch(() => [])) || [];
        const chat = chats.find((c) => String(c.id || "").includes(digits));
        await client.sendText(
          chat ? chat.id : `${digits}@c.us`,
          String(text).slice(0, 2000),
        );
        res.writeHead(200, { "content-type": "application/json" }).end('{"ok":true}');
      } catch {
        res.writeHead(500).end();
      }
    });
  }).listen(8090, () => console.log("send listener on :8090"));
}

// Persist the Chromium profile on the session volume — WhatsApp Web auth
// keys live in the browser profile (IndexedDB), so a tmp profile means a
// rescan after every container restart. Clear stale Singleton* locks left
// by unclean exits so Chrome will launch.
const profileDir = `${env.WA_SESSION_PATH || "./sessions"}/chrome-profile`;
for (const lock of ["SingletonLock", "SingletonSocket", "SingletonCookie"]) {
  try {
    unlinkSync(`${profileDir}/${lock}`);
  } catch {}
}

create({
  sessionId: "kaayal-demo",
  multiDevice: true,
  headless: true,
  qrTimeout: 0,
  authTimeout: 0,
  sessionDataPath: env.WA_SESSION_PATH || "./sessions",
  executablePath: env.WA_CHROME_PATH || undefined,
  chromiumArgs: [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    `--user-data-dir=${profileDir}`,
  ],
})
  .then(start)
  .catch((err) => {
    console.error("open-wa failed to start:", err);
    process.exit(1);
  });
