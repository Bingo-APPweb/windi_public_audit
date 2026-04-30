# W-MAIL-DACP-MILTER v1.0
# Spec: §227 W-MAIL-DACP-MILTER
#
# Postfix milter sidecar for DACP proof injection and Ledger sealing.
# MUST run BEFORE OpenDKIM in the milter chain.

FROM python:3.11-slim

LABEL maintainer="Liga IA+H <liga-iah@windisites.de>"
LABEL description="DACP Milter for WINDI Email Sovereign System"
LABEL version="1.0.0"
LABEL spec="§227 W-MAIL-DACP-MILTER"

# Install system dependencies for pymilter
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmilter-dev \
    gcc \
    libc6-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY tests/ ./tests/

# Create logs directory
RUN mkdir -p /logs

# Environment variables (can be overridden)
ENV DOMAIN=windisites.de
ENV LEDGER_URL=http://172.17.0.1:8101
ENV LEDGER_TIMEOUT=10
ENV RATE_LIMIT_PER_MIN=100
ENV LOG_PATH=/logs/dacp-milter.log
ENV LOG_LEVEL=INFO
ENV MILTER_SOCKET=inet:8890@0.0.0.0
ENV HTTP_ADMIN_PORT=8895
ENV DKIM_KEYS_PATH=/dkim/keys

# Expose ports
# 8890 - Milter protocol (for Postfix)
# 8895 - HTTP admin (health, metrics, version)
EXPOSE 8890 8895

# Health check via HTTP admin endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8895/health').read()" || exit 1

# Run the milter
CMD ["python", "dacp_milter.py"]
