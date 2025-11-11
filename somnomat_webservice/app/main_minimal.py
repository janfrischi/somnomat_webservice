"""
Minimal FastAPI server that uses Supabase API for most operations
while keeping some custom logic for convenience.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
import os

# Add parent directory to path to import supabase_api_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import supabase_api_client

app = FastAPI(title="SomnoMat Webservice (Minimal)", version="0.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Schemas ====================

class ReadingCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    heartrate: Optional[float] = Field(None, ge=0)
    hrv: Optional[float] = Field(None, ge=0)
    time_in_bed: Optional[float] = Field(None, ge=0)
    total_use_time: Optional[float] = Field(None, ge=0)
    timestamp: Optional[datetime] = None

class SleepSessionCreate(BaseModel):
    device_id: str
    session_start: datetime
    session_end: Optional[datetime] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    sleep_quality_score: Optional[int] = Field(None, ge=0, le=100)
    interruptions: int = 0
    notes: Optional[str] = None

# ==================== Health Check ====================

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "mode": "supabase-hybrid"}

# ==================== Readings (Custom Logic) ====================

@app.post("/api/v1/readings/", status_code=201)
def create_reading(payload: ReadingCreate):
    """
    Create a reading with automatic device creation.
    This is the convenience layer over Supabase.
    """
    try:
        # Check if device exists in Supabase
        devices = supabase_api_client.supabase.table("devices") \
            .select("id") \
            .eq("device_id", payload.device_id) \
            .execute()
        
        if devices.data:
            device_internal_id = devices.data[0]["id"]
        else:
            # Create device automatically
            new_device = supabase_api_client.supabase.table("devices") \
                .insert({"device_id": payload.device_id}) \
                .execute()
            device_internal_id = new_device.data[0]["id"]
        
        # Create reading
        reading_data = {
            "device_id": device_internal_id,
            "heartrate": payload.heartrate,
            "hrv": payload.hrv,
            "time_in_bed": payload.time_in_bed,
            "total_use_time": payload.total_use_time,
            "timestamp": (payload.timestamp or datetime.utcnow()).isoformat()
        }
        
        result = supabase_api_client.supabase.table("readings") \
            .insert(reading_data) \
            .execute()
        
        return result.data[0]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/readings/", tags=["readings"])
def list_readings(device_id: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Get readings with optional filtering."""
    try:
        query = supabase_api_client.supabase.table("readings") \
            .select("*, devices(device_id)")
        
        if device_id:
            # Get device internal ID first
            devices = supabase_api_client.supabase.table("devices") \
                .select("id") \
                .eq("device_id", device_id) \
                .execute()
            
            if devices.data:
                query = query.eq("device_id", devices.data[0]["id"])
        
        result = query \
            .order("timestamp", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {"items": result.data, "total": len(result.data)}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Sleep Sessions (Pure Supabase) ====================

@app.post("/api/v1/sleep-sessions/", status_code=201)
def create_sleep_session(payload: SleepSessionCreate):
    """Create sleep session using Supabase API directly."""
    session = supabase_api_client.create_sleep_session(
        device_id=payload.device_id,
        session_start=payload.session_start.isoformat(),
        session_end=payload.session_end.isoformat() if payload.session_end else None,
        duration_hours=payload.duration_hours,
        sleep_quality_score=payload.sleep_quality_score,
        interruptions=payload.interruptions,
        notes=payload.notes
    )
    return session

@app.get("/api/v1/sleep-sessions/", tags=["sleep-sessions"])
def list_sleep_sessions(device_id: Optional[str] = None, limit: int = 100):
    """Get sleep sessions."""
    return supabase_api_client.get_sleep_sessions(device_id, limit)

# ==================== Devices ====================

@app.get("/api/v1/devices/", tags=["devices"])
def list_devices(limit: int = 100, offset: int = 0):
    """List all devices."""
    result = supabase_api_client.supabase.table("devices") \
        .select("*") \
        .range(offset, offset + limit - 1) \
        .execute()
    return {"items": result.data, "total": len(result.data)}