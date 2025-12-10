FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY deployment/requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy source code
COPY src/ ./src/
COPY api/ ./api/
COPY configs/ ./configs/

# Create cache directory
RUN mkdir -p /app/cache/bert_embeddings

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
