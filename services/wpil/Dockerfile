# WINDI Verification API - WPIL
# Multi-stage build for minimal production image

FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY src/ ./src/

# Production image
FROM node:20-alpine

WORKDIR /app

# Security: run as non-root
RUN addgroup -g 1001 -S windi && \
    adduser -S windi -u 1001 -G windi

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src
COPY package.json ./

# Environment
ENV NODE_ENV=production
ENV PORT=4000
ENV HOST=0.0.0.0
ENV WPIL_MODE=relay
ENV LOG_LEVEL=info

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1

USER windi

EXPOSE 4000

CMD ["node", "src/server.js"]
