import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==================== Sleep Sessions API ====================

def create_sleep_session(
    device_id: str,
    session_start: str,
    session_end: Optional[str] = None,
    duration_hours: Optional[float] = None,
    sleep_quality_score: Optional[int] = None,
    interruptions: int = 0,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new sleep session using Supabase API."""
    data = {
        "device_id": device_id,
        "session_start": session_start,
        "session_end": session_end,
        "duration_hours": duration_hours,
        "sleep_quality_score": sleep_quality_score,
        "interruptions": interruptions,
        "notes": notes
    }
    
    response = supabase.table("sleep_sessions").insert(data).execute()
    return response.data[0] if response.data else None


def get_sleep_sessions(
    device_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get sleep sessions with optional filtering."""
    query = supabase.table("sleep_sessions").select("*")
    
    if device_id:
        query = query.eq("device_id", device_id)
    
    response = query \
        .order("session_start", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()
    
    return response.data


def get_session_by_id(session_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific sleep session by ID."""
    response = supabase.table("sleep_sessions") \
        .select("*") \
        .eq("id", session_id) \
        .execute()
    
    return response.data[0] if response.data else None


def update_sleep_session(session_id: int, **updates) -> Dict[str, Any]:
    """Update a sleep session."""
    response = supabase.table("sleep_sessions") \
        .update(updates) \
        .eq("id", session_id) \
        .execute()
    
    return response.data[0] if response.data else None


def delete_sleep_session(session_id: int) -> bool:
    """Delete a sleep session."""
    response = supabase.table("sleep_sessions") \
        .delete() \
        .eq("id", session_id) \
        .execute()
    
    return len(response.data) > 0


def get_sessions_by_date_range(
    device_id: str,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Get sleep sessions within a date range."""
    response = supabase.table("sleep_sessions") \
        .select("*") \
        .eq("device_id", device_id) \
        .gte("session_start", start_date) \
        .lte("session_start", end_date) \
        .order("session_start", desc=False) \
        .execute()
    
    return response.data


def get_average_sleep_quality(device_id: str) -> Optional[float]:
    """Calculate average sleep quality for a device."""
    sessions = supabase.table("sleep_sessions") \
        .select("sleep_quality_score") \
        .eq("device_id", device_id) \
        .not_.is_("sleep_quality_score", "null") \
        .execute()
    
    if not sessions.data:
        return None
    
    scores = [s["sleep_quality_score"] for s in sessions.data]
    return sum(scores) / len(scores) if scores else None


# ==================== Sleep Dashboard API ====================

def create_or_update_dashboard(
    device_id: int,  # Note: This is the internal device ID (foreign key)
    sleep_consistency: Optional[float] = None,
    bedtime_consistency: Optional[float] = None,
    bed_use: Optional[float] = None,
    daily_occupancy: Optional[float] = None,
    total_intervals: Optional[float] = None,
    total_nights: Optional[float] = None,
    avg_sleep_per_night: Optional[float] = None,
    suggestion_awakening: Optional[str] = None,
    suggestion_avg_sleep: Optional[str] = None,
    suggestion_consistency: Optional[str] = None,
    suggestion_bed_use: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create or update dashboard metrics for a device.
    Uses upsert to update if exists, create if not.
    """
    data = {
        "id": device_id,  # This is both the primary key and foreign key
        "sleep_consistency": sleep_consistency,
        "bedtime_consistency": bedtime_consistency,
        "bed_use": bed_use,
        "daily_occupany": daily_occupancy,  # Note: typo in your schema "occupany"
        "total_intervals": total_intervals,
        "total_nights": total_nights,
        "avg_sleep_per_night": avg_sleep_per_night,
        "suggestion_awakening": suggestion_awakening,
        "suggestion_avg_sleep": suggestion_avg_sleep,
        "suggestion_consistency": suggestion_consistency,
        "suggestion_bed_use": suggestion_bed_use
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    response = supabase.table("sleep_dashboard") \
        .upsert(data, on_conflict="id") \
        .execute()
    
    return response.data[0] if response.data else None


def get_dashboard(device_id: int) -> Optional[Dict[str, Any]]:
    """Get dashboard metrics for a device."""
    response = supabase.table("sleep_dashboard") \
        .select("*") \
        .eq("id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_dashboard_with_device(device_id: int) -> Optional[Dict[str, Any]]:
    """Get dashboard metrics with device information."""
    response = supabase.table("sleep_dashboard") \
        .select("*, devices(device_id, name, boardtype)") \
        .eq("id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def delete_dashboard(device_id: int) -> bool:
    """Delete dashboard metrics for a device."""
    response = supabase.table("sleep_dashboard") \
        .delete() \
        .eq("id", device_id) \
        .execute()
    
    return len(response.data) > 0


# ==================== Devices API ====================

def get_device_by_string_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Get device by string device_id (e.g., 'esp32-a1')."""
    response = supabase.table("devices") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_device_by_internal_id(id: int) -> Optional[Dict[str, Any]]:
    """Get device by internal integer ID."""
    response = supabase.table("devices") \
        .select("*") \
        .eq("id", id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices."""
    response = supabase.table("devices") \
        .select("*") \
        .execute()
    
    return response.data