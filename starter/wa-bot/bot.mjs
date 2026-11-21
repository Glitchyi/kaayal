// Kaayal WhatsApp demo onboarding bot — unofficial whatsapp-web.js session.
// Pair the 9400354625 phone via the QR this prints on first run, keep it
// running, and inbound DMs get a 3-step onboarding flow ending in a
// one-time operator portal link issued by the Kaayal API.
//
// DEMO ONLY: whatsapp-web.js automates WhatsApp Web (unofficial, ToS risk).
// Production path is the WhatsApp Business API.

import pkg from "whatsapp-web.js";
import qrcode from "qrcode-terminal";
import { readFileSync, unlinkSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const { Client, LocalAuth } = pkg;

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

async function onboard({ phone, name, boat_name, boat_type, embarkation }) {
  const res = await fetch(`${API}/api/ops/wa_onboard`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Kaayal-Tool-Token": TOKEN },
    body: JSON.stringify({ phone, name, boat_name, boat_type, embarkation }),
  });
  if (!res.ok) throw new Error(`onboard failed: HTTP ${res.status}`);
  return res.json();
}

// Voice notes: download+decrypt via the session, transcribe server-side
// (OpenAI key never leaves the app container).
async function transcribe(msg) {
  const media = await msg.downloadMedia();
  if (!media?.data) throw new Error("no media");
  const audio_b64 = media.data;
  const mimetype = media.mimetype || "audio/ogg";
  const res = await fetch(`${API}/api/ops/wa_transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Kaayal-Tool-Token": TOKEN },
    body: JSON.stringify({ audio_b64, mimetype }),
  });
  if (!res.ok) throw new Error(`transcribe failed: HTTP ${res.status}`);
  return (await res.json()).text || "";
}

// Operator manages bookings/reachability by chat command.
async function opsCall(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Kaayal-Tool-Token": TOKEN },
    body: JSON.stringify(body),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${path} failed: HTTP ${res.status}`);
  return res.json();
}

const HELP =
  "Kaayal operator commands:\n" +
  "• REQUESTS — list pending booking requests\n" +
  "• REQ-XXXX-XXXX — confirm a request (sends you the caller's number)\n" +
  "• DECLINE REQ-XXXX-XXXX — decline it\n" +
  "• PAUSE / RESUME — stop/start being reachable to callers\n" +
  "• HELP — this list";

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

// whatsapp-web.js message shape → normalize once so the flow below stays
// library-agnostic. DM ids look like '91xx@c.us'; groups are '@g.us'.
function chatIdOf(msg) {
  return msg.fromMe ? msg.to : msg.from;
}

function start(client) {
  const sendText = (chatId, text) => client.sendMessage(chatId, text);
  console.log("Kaayal wa-bot connected. Waiting for DMs…");
  client.on("message", async (msg) => {
    try {
      const isGroup = String(msg.from).endsWith("@g.us");
      // Log shape only — never the raw phone number or body (PII rules).
      console.log(
        `inbound msg: type=${msg.type} group=${isGroup} fromMe=${!!msg.fromMe} from=…${String(msg.from || "").replace(/@.*/, "").slice(-4)}`
      );
      const isVoice = ["ptt", "audio"].includes(msg.type);
      if (msg.fromMe || isGroup || (msg.type !== "chat" && !isVoice)) return;
      const chatId = chatIdOf(msg);
      const phone = String(msg.from).replace(/@.*/, "");
      let text = (msg.body || "").trim();
      if (isVoice) {
        await sendText(chatId, "Got your voice note — one second…");
        try {
          text = (await transcribe(msg)).trim();
        } catch {
          await sendText(
            chatId,
            "Sorry, I couldn't hear that voice note — please type it instead."
          );
          return;
        }
      }
      if (!text) return;

      // Operator commands — checked before the onboarding flow; a 404
      // (unknown number) falls through to onboarding for list-type commands.
      const cmd = text.trim().toUpperCase();
      const idMatch = text.match(/\b(REQ-\d{3,}-[0-9a-f]{2,})\b/i);

      if (idMatch) {
        const action = cmd.startsWith("DECLINE") ? "decline" : "confirm";
        const c = await opsCall("/api/ops/wa_confirm", {
          phone, request_id: idMatch[1].toUpperCase(), action,
        });
        await sendText(
          chatId,
          c === null
            ? `Couldn't find ${idMatch[1].toUpperCase()} for your number — check the ID and reply again.`
            : c.status === "confirmed"
              ? `Confirmed ✅ ${c.request_id}\n` +
                `Caller: ${c.customer_name} — ${c.customer_phone}\n` +
                `${c.boat_name || "—"}${c.preferred_date ? ` · ${c.preferred_date}` : ""}${c.group_size ? ` · ${c.group_size} people` : ""}\n` +
                (c.notify_channel === "call"
                  ? "We called them with the good news — they're expecting your call."
                  : c.notify_channel === "whatsapp"
                    ? "Couldn't reach them by call, so they were WhatsApped the confirmation — expecting your call."
                    : "Confirmation call is queued — do call their number in the meantime.")
              : c.status === "declined"
                ? `${c.request_id} declined. The caller can leave a callback request instead.`
                : `${c.request_id} is already ${c.status} — nothing to do.`,
        );
        return;
      }
      if (cmd === "REQUESTS") {
        const r = await opsCall("/api/ops/wa_requests", { phone });
        if (r === null) {
          // Unknown number → onboarding flow below.
        } else {
          await sendText(
            chatId,
            r.requests.length
              ? "Pending requests:\n" +
                r.requests
                  .map((x) =>
                    `• ${x.request_id} — ${x.boat_name || "general"}` +
                    ` — ${x.customer_name}` +
                    `${x.preferred_date ? ` · ${x.preferred_date}` : ""}` +
                    `${x.group_size ? ` · ${x.group_size} people` : ""}`
                  )
                  .join("\n") +
                "\n\nReply with a request ID to confirm, or DECLINE <id>."
              : "No pending requests right now."
          );
          return;
        }
      }
      if (cmd === "PAUSE" || cmd === "RESUME") {
        const r = await opsCall("/api/ops/wa_reachable", {
          phone, reachable: cmd === "RESUME",
        });
        if (r !== null) {
          await sendText(
            chatId,
            r.reachable
              ? "You're reachable again — callers can reach you and queued callbacks will fire."
              : "You're now unreachable — callers will be offered a callback instead."
          );
          return;
        }
      }
      if (cmd === "HELP") {
        await sendText(chatId, HELP);
        return;
      }

      const s = state.get(chatId) || { step: 0 };

      if (s.step === 0) {
        const known = await reissue(phone);
        if (known) {
          await sendText(
            chatId,
            known.portal_url
              ? `Welcome back, ${known.name}!\n\n` +
                  `Fresh portal link (the old one just died):\n${known.portal_url}`
              : `You're already registered, ${known.name} — still *pending verification*. ` +
                  "We'll WhatsApp you the portal link once the owner approves."
          );
        } else {
          await sendText(chatId, WELCOME);
          state.set(chatId, { step: 1 });
        }
      } else if (s.step === 1) {
        s.name = text;
        await sendText(
          chatId,
          `Thanks ${text}! Now send your boat as *name, type, embarkation* ` +
            '(e.g. "Queen, houseboat, Punnamada") — or reply "skip" if you\'ll add boats later.'
        );
        s.step = 2;
        state.set(chatId, s);
      } else if (s.step === 2) {
        s.boat = null;
        if (text.toLowerCase() !== "skip") {
          // "name, type, embarkation" — 2 parts = name + embarkation.
          const [b, t, e] = text.split(",").map((x) => x.trim());
          s.boat = e
            ? { name: b || null, type: t || null, embark: e }
            : { name: b || null, type: null, embark: t || null };
        }
        const boatLine = s.boat?.name
          ? `Boat: ${s.boat.name}` +
            (s.boat.type ? ` (${s.boat.type})` : "") +
            (s.boat.embark ? ` from ${s.boat.embark}` : "")
          : "No boat yet (add it later from the portal)";
        await sendText(
          chatId,
          `Just to confirm:\n• Name: ${s.name}\n• ${boatLine}\n\n` +
            "Reply *YES* to register or *NO* to start over."
        );
        s.step = 3;
        state.set(chatId, s);
      } else if (s.step === 3) {
        const ans = text.toLowerCase();
        if (ans === "no") {
          state.set(chatId, { step: 1 });
          await sendText(chatId, "No problem — let's start over. What's your name?");
          return;
        }
        if (ans !== "yes") {
          await sendText(chatId, "Reply *YES* to register or *NO* to start over.");
          return;
        }
        const r = await onboard({
          phone,
          name: s.name,
          boat_name: s.boat?.name || null,
          boat_type: s.boat?.type || null,
          embarkation: s.boat?.embark || null,
        });
        await sendText(
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
        await sendText(msg.chatId, "Sorry, something went wrong on our side — please try again in a moment.");
      } catch {
        /* nothing else we can do */
      }
    }
  });
  // Diagnostic: fires for every message event, not just inbound chats.
  client.on("message_create", (msg) => {
    console.log(
      `any-msg: type=${msg.type} group=${String(msg.from || "").endsWith("@g.us")} fromMe=${!!msg.fromMe}`
    );
  });
  // Push channel for the app: POST /send {phone, text} authed with the shared
  // tool token — delivers messages without an inbound DM (e.g. portal link
  // on operator approval, or to numbers that have never DM'd — whatsapp-web.js
  // has no new-chat license gate, though WhatsApp-side spam limits still
  // apply, so this stays demo-only). Internal network only, never published.
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
        // Plain-text send built on the raw WA modules — the same calls
        // client.sendMessage makes, minus the broken WWebJS injection
        // layer. Works for new chats too (findOrCreateLatestChat).
        const result = await client.pupPage.evaluate(
          async (jid, body) => {
            const R = window.require;
            const chatWid = R("WAWebWidFactory").createWid(jid);
            let chat = R("WAWebCollections").Chat.get(chatWid);
            if (!chat) {
              chat = (await R("WAWebFindChatAction").findOrCreateLatestChat(chatWid))?.chat;
            }
            if (!chat) return "no_chat";
            const { getMaybeMeLidUser, getMaybeMePnUser } = R("WAWebUserPrefsMeUser");
            const from = chat.id.isLid?.() ? getMaybeMeLidUser() : getMaybeMePnUser();
            const newId = await R("WAWebMsgKey").newId();
            const newMsgKey = new (R("WAWebMsgKey"))({
              from, to: chat.id, id: newId, selfDir: "out",
            });
            const ephemeralFields =
              R("WAWebGetEphemeralFieldsMsgActionsUtils").getEphemeralFields(chat);
            const message = {
              id: newMsgKey, ack: 0, body, from, to: chat.id, local: true,
              self: "out", t: parseInt(Date.now() / 1000),
              isNewMsg: true, type: "chat", ...ephemeralFields,
            };
            if (message.__x_id) delete message.__x_id;
            const [msgPromise] = R("WAWebSendMsgChatAction").addAndSendMsgToChat(chat, message);
            await msgPromise;
            return "sent";
          },
          `${digits}@c.us`,
          String(text).slice(0, 2000),
        );
        console.log("raw send result:", result);
        if (result !== "sent") throw new Error(String(result));
        res.writeHead(200, { "content-type": "application/json" }).end('{"ok":true}');
      } catch (err) {
        console.log("/send failed:", err?.message || err);
        res.writeHead(500).end();
      }
    });
  }).listen(8090, () => console.log("send listener on :8090"));
}

// LocalAuth persists the linked-device session on the volume so restarts
// don't need a rescan. Clear stale Chrome Singleton* locks left by unclean
// exits so the profile will launch.
const sessionDir = `${env.WA_SESSION_PATH || "./sessions"}/session-kaayal-demo`;
for (const lock of ["SingletonLock", "SingletonSocket", "SingletonCookie"]) {
  try {
    unlinkSync(`${sessionDir}/${lock}`);
  } catch {}
}

const client = new Client({
  authStrategy: new LocalAuth({
    clientId: "kaayal-demo",
    dataPath: env.WA_SESSION_PATH || "./sessions",
  }),
  puppeteer: {
    headless: true,
    executablePath: env.WA_CHROME_PATH || undefined,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
});

client.on("loading_screen", (pct, msg) => console.log(`loading: ${pct}% ${msg}`));

client.on("qr", (qr) => {
  console.log("=== SCAN THIS QR (WhatsApp → Linked devices → Link a device) ===");
  qrcode.generate(qr, { small: true });
});
let booted = false;
const boot = (via) => {
  if (booted) return;
  booted = true;
  console.log(`wa-bot starting (${via})`);
  start(client);
};
client.on("ready", () => boot("ready"));
let reinjected = false;
client.on("authenticated", () => {
  console.log("wa-bot authenticated");
  if (reinjected) return; // inject() re-emits authenticated — only arm once
  reinjected = true;
  // Upstream race (issue 201987): 'ready' is gated on a hasSynced event that
  // can be missed on warm reinjects. Poll the socket state directly and
  // start once the session reports CONNECTED.
  let injecting = false;
  const iv = setInterval(async () => {
    try {
      if ((await client.getState()) !== "CONNECTED") return;
      // Socket is up — but 'ready' needs window.WWebJS injected. If the
      // first inject attempt died silently (its rejection happens inside
      // the page), retry it ourselves and log the real error.
      const storeReady = await client.pupPage
        .evaluate(() => typeof window.WWebJS !== "undefined")
        .catch(() => false);
      if (storeReady) {
        clearInterval(iv);
        boot("state=CONNECTED fallback");
      } else {
        // WWebJS never materializes on this WA Web build (upstream inject is
        // broken). Our send path uses raw window.require modules directly —
        // it doesn't need WWebJS at all, so boot anyway.
        clearInterval(iv);
        boot("state=CONNECTED fallback (raw-require send path)");
      }
    } catch (e) {
      console.log("state poll not ready:", e?.message || e);
    }
  }, 5000);
  setTimeout(() => clearInterval(iv), 300000);
});
client.on("auth_failure", (m) => {
  console.error("auth failure:", m);
  process.exit(1);
});
client.on("disconnected", (reason) => {
  console.error("disconnected:", reason, "— exiting for restart");
  process.exit(1);
});
client.initialize();
