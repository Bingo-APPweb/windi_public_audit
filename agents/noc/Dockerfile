# WINDI NOC Agent - Dockerfile
FROM python:3.11-slim

LABEL maintainer="WINDI Platform <dev@windi.tech>"
LABEL description="WINDI NOC Agent - Network Operations Center"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY noc_agent.py .
COPY config/ ./config/
COPY collectors/ ./collectors/
COPY analyzers/ ./analyzers/
COPY alerting/ ./alerting/

# Create directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NOC_CONFIG=/app/config/noc_config.yaml

# Expose port
EXPOSE 8880

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8880/health || exit 1

# Run the agent
CMD ["python", "noc_agent.py"]
