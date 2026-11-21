# Kaayal wa-bot — open-wa demo sidecar. Unofficial API, demo only.
FROM node:20-bookworm-slim

# System chromium (+ its shared libs) for puppeteer; fonts so QR/pages render.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-noto-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /bot
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY bot.mjs ./

# Named volume inherits ownership: paired WhatsApp session lives here.
RUN mkdir -p /session && chown -R node:node /session
USER node

ENV KAAYAL_API_BASE="http://app:8000" \
    WA_SESSION_PATH="/session" \
    WA_CHROME_PATH="/usr/bin/chromium"
CMD ["node", "bot.mjs"]
