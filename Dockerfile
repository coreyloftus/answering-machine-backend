# Use a slim Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV PORT 8080 # Cloud Run expects applications to listen on port 8080

# Create and set working directory
WORKDIR $APP_HOME

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy your application code
# Adjust this if your FastAPI code is in a subdirectory (e.g., 'src')
COPY . $APP_HOME

# Command to run your application when the container starts
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
