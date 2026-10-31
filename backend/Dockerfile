# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system certificates and curl for network operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with UID 1000 for Hugging Face Docker Spaces
RUN useradd -m -u 1000 user

# Configure environment variables for Python, FastEmbed, and ChromaDB
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed \
    CHROMA_DB_DIR=/app/data/chroma_db

WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application source and reference datasets
COPY . /app

# Pre-warm FastEmbed embedding model and populate the 125-chunk ChromaDB collection at build time
RUN python scripts/build_vector_index.py && \
    chown -R user:user /app /home/user

# Switch to non-root user
USER user

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Launch FastAPI via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
