# Application entry point for the Somnomat Webservice

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
# Import routers/endpoints
from app.routers import readings, devices

# Create tables defined in app/models.py
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(title=settings.api_title, version=settings.api_version)

# Configure CORS middleware if allowed origins are specified
if settings.allowed_origins:
    app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Simple health check endpoint
@app.get("/health", tags=["meta"])

def root():
    return {"message": "Somnomat Webservice is running!"}
def health():
    return {"status": "ok"}

# Register routers
app.include_router(devices.router, prefix="/api/v1")
app.include_router(readings.router, prefix="/api/v1")
