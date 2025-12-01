# Streamlit + Google ADK deployment for Cloud Run
FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies (optional: curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Google ADK from the vendored source tree
COPY adk-python ./adk-python
RUN pip install --no-cache-dir ./adk-python

# Copy application source
COPY src ./src
COPY ui ./ui
COPY assets ./assets
COPY data ./data
COPY docs ./docs

ENV PYTHONPATH=/app/src \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

EXPOSE 8080

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
