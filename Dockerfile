# AI Peer Review - Backend Dockerfile for GCP Cloud Run
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY main.py .

# Cloud Run uses PORT environment variable
ENV PORT=8080

# Run the application
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}

