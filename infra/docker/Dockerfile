FROM python:3.10-slim

WORKDIR /app

# Install system deps for geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Generate fixture data for demo/testing
RUN python tests/fixtures/generate_fixtures.py

# Expose API and dashboard ports
EXPOSE 8000 8501

# Default: run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
