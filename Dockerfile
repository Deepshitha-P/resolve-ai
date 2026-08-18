# Use a lightweight python runtime as base image
FROM python:3.11-slim

# Install system dependencies needed to compile any C/C++ extensions (like scikit-learn or pyarrow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to take advantage of docker layer caching
COPY requirements.txt /app/

# Install Python packages
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy models (small for CPUs, trf for GPU/high-resource environments)
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download en_core_web_trf || true

# Copy all application files (excluding those in .dockerignore)
COPY . /app

# Expose the API server port
EXPOSE 8000

# Prevent python from buffering stdout/stderr (enables real-time logs in docker container logs)
ENV PYTHONUNBUFFERED=1

# Command to execute the application
CMD uvicorn backend.app:app --host 0.0.0.0 --port $PORT
