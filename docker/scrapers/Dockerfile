# NBA Scraper Dockerfile
# Multi-stage build for NBA data scrapers

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN groupadd -r scraper && useradd -r -g scraper scraper

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p logs data checkpoints && \
    chown -R scraper:scraper /app

# Switch to unprivileged user
USER scraper

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Default command (can be overridden)
CMD ["python", "scripts/etl/espn_async_scraper.py"]







