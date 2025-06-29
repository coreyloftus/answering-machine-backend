from fastapi import FastAPI
import os

app = FastAPI(title="Answering Machine API", version="1.0.0")

# Add startup logging
print("Starting Answering Machine API...")
print("FastAPI app created successfully")

# Update origins to include Cloud Run URLs
origins = [
    "http://localhost:3000",
    "http://192.168.86.77:3000",
    "https://*.run.app",  # Allow Cloud Run URLs
    "*",  # Allow all origins for development
]

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT"],
    allow_headers=["*"],
)

print("CORS middleware added successfully")


@app.get("/")
async def root():
    """Health check endpoint"""
    print("Root endpoint called")
    return {"message": "Answering Machine API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    print("Health check endpoint called")
    return {"status": "healthy", "service": "answering-machine-api"}


@app.get("/test")
async def test():
    """Simple test endpoint"""
    print("Test endpoint called")
    return {"message": "Test endpoint working"}


print("All endpoints registered successfully")
print("Application startup complete")
