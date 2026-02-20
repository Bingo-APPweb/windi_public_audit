# ═══════════════════════════════════════════════════════════════════
# WINDI Merkle Anchor Log — Dockerfile
# ═══════════════════════════════════════════════════════════════════
# CT-style Merkle Transparency Log for document anchors
# Port: 4051
# ═══════════════════════════════════════════════════════════════════

FROM node:20-alpine

LABEL maintainer="WINDI Project"
LABEL description="Merkle Transparency Log for WINDI Phase 3"

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm install --omit=dev

# Copy source
COPY src/ ./src/
COPY sql/ ./sql/

# Environment defaults
ENV NODE_ENV=production
ENV PORT=4051
ENV LOG_KEY_ID=hub-log-2026

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:4051/health || exit 1

EXPOSE 4051

CMD ["node", "src/server.js"]
