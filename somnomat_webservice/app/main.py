# Application entry point for the Somnomat Webservice

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
# Import routers/endpoints
from app.routers import readings, devices

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.api_title, version=settings.api_version)

if settings.allowed_origins:
    app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

@app.get("/health", tags=["meta"])
def root():
    return {"message": "Somnomat Webservice is running!"}
def health():
    return {"status": "ok"}

# Plug routers into main app
app.include_router(devices.router, prefix="/api/v1")
app.include_router(readings.router, prefix="/api/v1")
