import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL_CALMEA")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_CALMEA")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL_CALMEA and SUPABASE_KEY_CALMEA must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==================== Devices API ====================

def create_device(
    name: str,
    boardtype: Optional[int] = None,
    mac: Optional[str] = None,
    hardware_version: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new device."""
    data = {
        "name": name,
        "boardtype": boardtype,
        "mac": mac,
        "hardware_version": hardware_version
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    response = supabase.table("devices") \
        .insert(data) \
        .execute()
    
    return response.data[0] if response.data else None


def get_device_by_id(device_id: int) -> Optional[Dict[str, Any]]:
    """Get device by ID."""
    response = supabase.table("devices") \
        .select("*") \
        .eq("id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices."""
    response = supabase.table("devices") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    
    return response.data


def update_device(device_id: int, **updates) -> Dict[str, Any]:
    """Update a device."""
    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}
    
    response = supabase.table("devices") \
        .update(updates) \
        .eq("id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def delete_device(device_id: int) -> bool:
    """Delete a device."""
    try:
        response = supabase.table("devices") \
            .delete() \
            .eq("id", device_id) \
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting device: {e}")
        return False


# ==================== Firmware API ====================

def create_firmware(
    version: str,
    binary_file: Optional[str] = None,
    significance_level: Optional[int] = None,
    partition: Optional[int] = None,
    version_ota1: Optional[str] = None,
    version_ota2: Optional[str] = None,
    sd_free_storage: Optional[int] = None,
    device_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new firmware entry."""
    data = {
        "version": version,
        "binary_file": binary_file,
        "significance_level": significance_level,
        "partition": partition,
        "version_ota1": version_ota1,
        "version_ota2": version_ota2,
        "sd_free_storage": sd_free_storage,
        "device_id": device_id
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    response = supabase.table("firmware") \
        .insert(data) \
        .execute()
    
    return response.data[0] if response.data else None


def get_firmware_by_id(firmware_id: int) -> Optional[Dict[str, Any]]:
    """Get firmware by ID."""
    response = supabase.table("firmware") \
        .select("*") \
        .eq("id", firmware_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_firmware_by_device(device_id: int) -> List[Dict[str, Any]]:
    """Get all firmware for a specific device."""
    response = supabase.table("firmware") \
        .select("*") \
        .eq("device_id", device_id) \
        .order("last_seen", desc=True) \
        .execute()
    
    return response.data


def get_latest_firmware_version() -> Optional[Dict[str, Any]]:
    """Get the latest firmware version."""
    response = supabase.table("firmware") \
        .select("*") \
        .order("version", desc=True) \
        .limit(1) \
        .execute()
    
    return response.data[0] if response.data else None


def update_firmware(firmware_id: int, **updates) -> Dict[str, Any]:
    """Update firmware entry."""
    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}
    
    response = supabase.table("firmware") \
        .update(updates) \
        .eq("id", firmware_id) \
        .execute()
    
    return response.data[0] if response.data else None


def update_firmware_last_seen(firmware_id: int) -> Dict[str, Any]:
    """Update the last_seen timestamp for firmware."""
    response = supabase.table("firmware") \
        .update({"last_seen": datetime.now(timezone.utc).isoformat()}) \
        .eq("id", firmware_id) \
        .execute()
    
    return response.data[0] if response.data else None


# ==================== User Settings API ====================

def create_user_settings(
    device_id: int,
    amplitude: Optional[int] = None,
    frequency: Optional[int] = None,
    vibration: Optional[int] = None
) -> Dict[str, Any]:
    """Create or update user settings for a device."""
    data = {
        "device_id": device_id,
        "amplitude": amplitude,
        "frequency": frequency,
        "vibration": vibration
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    # Use upsert to update if exists
    response = supabase.table("user_settings") \
        .upsert(data, on_conflict="device_id") \
        .execute()
    
    return response.data[0] if response.data else None


def get_user_settings_by_id(settings_id: int) -> Optional[Dict[str, Any]]:
    """Get user settings by ID."""
    response = supabase.table("user_settings") \
        .select("*") \
        .eq("id", settings_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_user_settings_by_device(device_id: int) -> Optional[Dict[str, Any]]:
    """Get user settings for a specific device."""
    response = supabase.table("user_settings") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def update_user_settings(settings_id: int, **updates) -> Dict[str, Any]:
    """Update user settings."""
    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}
    
    response = supabase.table("user_settings") \
        .update(updates) \
        .eq("id", settings_id) \
        .execute()
    
    return response.data[0] if response.data else None


def delete_user_settings(settings_id: int) -> bool:
    """Delete user settings."""
    try:
        response = supabase.table("user_settings") \
            .delete() \
            .eq("id", settings_id) \
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting user settings: {e}")
        return False


# ==================== Raw Occupancy API ====================

def create_raw_occupancy(
    device_id: int,
    occupied: bool,
    created_at: Optional[str] = None  # Add this parameter
) -> Dict[str, Any]:
    """Create a new raw occupancy reading."""
    from datetime import datetime, timezone
    
    data = {
        "device_id": device_id,
        "occupied": occupied,
        "created_at": created_at or datetime.now(timezone.utc).isoformat()  # Use provided timestamp or default to now
    }
    
    response = supabase.table("raw_occupancy") \
        .insert(data) \
        .execute()
    
    return response.data[0] if response.data else None


def create_bulk_raw_occupancy(
    device_id: int,
    readings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Create multiple raw occupancy readings at once.
    
    Args:
        device_id: The device ID
        readings: List of dicts with 'occupied' (bool) and 'created_at' (str) keys
    
    Returns:
        List of created readings
    """
    data = [
        {
            "device_id": device_id,
            "occupied": reading["occupied"],
            "created_at": reading["created_at"]
        }
        for reading in readings
    ]
    
    # Supabase supports bulk insert (up to 1000 rows at a time)
    response = supabase.table("raw_occupancy") \
        .insert(data) \
        .execute()
    
    return response.data if response.data else []


def get_raw_occupancy_by_id(occupancy_id: int) -> Optional[Dict[str, Any]]:
    """Get raw occupancy by ID."""
    response = supabase.table("raw_occupancy") \
        .select("*") \
        .eq("id", occupancy_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_raw_occupancy_by_device(
    device_id: int,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get raw occupancy readings for a device."""
    response = supabase.table("raw_occupancy") \
        .select("*") \
        .eq("device_id", device_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()
    
    return response.data


def get_raw_occupancy_by_date_range(
    device_id: int,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Get raw occupancy readings within a date range."""
    response = supabase.table("raw_occupancy") \
        .select("*") \
        .eq("device_id", device_id) \
        .gte("created_at", start_date) \
        .lte("created_at", end_date) \
        .order("created_at", desc=False) \
        .execute()
    
    return response.data


def get_current_occupancy_status(device_id: int) -> Optional[bool]:
    """Get the most recent occupancy status for a device."""
    response = supabase.table("raw_occupancy") \
        .select("occupied") \
        .eq("device_id", device_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    
    return response.data[0]["occupied"] if response.data else None


# ==================== Sleep Dashboard API ====================

def create_or_update_dashboard(
    device_id: int,
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
    """Create or update dashboard metrics for a device."""
    # First, check if a dashboard already exists for this device
    existing = supabase.table("sleep_dashboard") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()
    
    data = {
        "device_id": device_id,  # This is the foreign key - MUST be set!
        "sleep_consistency": sleep_consistency,
        "bedtime_consistency": bedtime_consistency,
        "bed_use": bed_use,
        "daily_occupancy": daily_occupancy,
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
    
    if existing.data:
        # Update existing dashboard
        response = supabase.table("sleep_dashboard") \
            .update(data) \
            .eq("device_id", device_id) \
            .execute()
    else:
        # Insert new dashboard
        response = supabase.table("sleep_dashboard") \
            .insert(data) \
            .execute()
    
    return response.data[0] if response.data else None


def get_dashboard(device_id: int) -> Optional[Dict[str, Any]]:
    """Get dashboard metrics for a device."""
    response = supabase.table("sleep_dashboard") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def get_dashboard_with_device(device_id: int) -> Optional[Dict[str, Any]]:
    """Get dashboard metrics with device information."""
    response = supabase.table("sleep_dashboard") \
        .select("*, devices(name, boardtype, mac, hardware_version)") \
        .eq("device_id", device_id) \
        .execute()
    
    return response.data[0] if response.data else None


def delete_dashboard(device_id: int) -> bool:
    """Delete dashboard metrics for a device."""
    try:
        response = supabase.table("sleep_dashboard") \
            .delete() \
            .eq("device_id", device_id) \
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting dashboard: {e}")
        return False


# ==================== Helper Functions ====================

def get_device_with_all_data(device_id: int) -> Optional[Dict[str, Any]]:
    """Get device with all related data (firmware, settings, dashboard)."""
    device = get_device_by_id(device_id)
    if not device:
        return None
    
    device['firmware'] = get_firmware_by_device(device_id)
    device['settings'] = get_user_settings_by_device(device_id)
    device['dashboard'] = get_dashboard(device_id)
    device['current_occupancy'] = get_current_occupancy_status(device_id)
    
    return device