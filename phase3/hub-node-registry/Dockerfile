# ═══════════════════════════════════════════════════════════════════
# WINDI Hub Node Registry - Dockerfile
# ═══════════════════════════════════════════════════════════════════

FROM node:20-alpine

LABEL maintainer="WINDI Team"
LABEL description="Hub Node Registry for WINDI Phase 3 Federation"

WORKDIR /app

# Install dependencies first for caching
COPY package.json ./
RUN npm install --production

# Copy application
COPY src/ ./src/
COPY sql/ ./sql/

# Environment
ENV NODE_ENV=production
ENV PORT=8070

EXPOSE 8070

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8070/health || exit 1

CMD ["node", "src/server.js"]
