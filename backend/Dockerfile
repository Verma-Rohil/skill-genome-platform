# Stage 1: Builder stage to compile wheels and install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for compiling packages (e.g. rapidfuzz, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install packages into root local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime runner stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy the compiled packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy project source code
COPY app /app/app
COPY data /app/data
COPY ml /app/ml

# Pre-download and bake S-BERT model weights into the image cache.
# This prevents runtime startup delays and allows offline execution.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Expose FastAPI default port
EXPOSE 8000

# Start FastAPI application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
