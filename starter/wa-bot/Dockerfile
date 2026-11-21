# Kaayal wa-bot — whatsapp-web.js demo sidecar. Unofficial API, demo only.
FROM node:22-bookworm-slim

# System chromium (+ its shared libs) for puppeteer; fonts so QR/pages render.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-noto-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /bot
COPY package.json package-lock.json ./
# whatsapp-web.js pulls puppeteer — don't let it download Chrome; we use
# the system chromium via WA_CHROME_PATH.
ENV PUPPETEER_SKIP_DOWNLOAD=1 \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1
RUN npm ci --omit=dev
COPY bot.mjs ./

# Named volume inherits ownership: paired WhatsApp session lives here.
RUN mkdir -p /session && chown -R node:node /session
USER node

ENV KAAYAL_API_BASE="http://app:8000" \
    WA_SESSION_PATH="/session" \
    WA_CHROME_PATH="/usr/bin/chromium"
CMD ["node", "bot.mjs"]
