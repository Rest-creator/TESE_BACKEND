# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# 1. Install System Dependencies
# Required for Postgres (psycopg2), compiling C extensions, and netcat for entrypoint
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python Dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Daphne explicitly (Required for WebSockets)
RUN pip install daphne

# 3. Copy Source Code
# We use "." because the build context is already inside the Backend folder
COPY . .

# Expose port
EXPOSE 8000

# 4. Run ASGI Server (Daphne)
# Critical: Use 'daphne' instead of 'gunicorn' for WebSockets support
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "teseapp.asgi:application"]