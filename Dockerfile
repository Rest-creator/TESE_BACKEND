# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY Backend/ .

# Expose port
EXPOSE 8000

# Run Django server
CMD ["gunicorn", "teseapp.wsgi:application", "--bind", "0.0.0.0:8000"]
