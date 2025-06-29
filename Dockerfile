# Use a slim Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app
ENV PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  curl &&
  rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR $APP_HOME

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip &&
  pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . $APP_HOME

# Make startup script executable
RUN chmod +x start.sh

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser &&
  chown -R appuser:appuser $APP_HOME
USER appuser

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Command to run your application when the container starts
CMD ["./start.sh"]
