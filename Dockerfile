# Production Dockerfile for Minh An Technology Solutions
FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing bytecode and enable immediate log streaming
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose default HTTP port
EXPOSE 8080

# Run server
CMD ["python", "server.py"]

