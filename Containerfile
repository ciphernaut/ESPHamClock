# Use a lightweight Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (none needed for now besides requests)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (we'll just use pip install directly for simple deps)
RUN pip install --no-cache-dir requests

# Copy source code
COPY server.py .
COPY shadow_proxy/ shadow_proxy/
COPY ingestion/ ingestion/

# Create data directories
RUN mkdir -p processed_data/NOAASpaceWX \
    && mkdir -p processed_data/weather \
    && mkdir -p captured_data

# The actual configuration for which service to run will be in podman-compose.yml
# But we can provide a default
CMD ["python3", "server.py"]
