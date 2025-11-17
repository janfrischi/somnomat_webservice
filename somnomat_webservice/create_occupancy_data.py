"""
Create realistic occupancy data for testing the dashboard.
Simplified version - use setup_device.py for complete device setup.
"""
from supabase_api_client_somnomat import create_raw_occupancy, get_device_by_id
from datetime import datetime, timedelta, timezone
import sys
import random


def create_realistic_occupancy(device_id: int, days: int = 7):
    """Generate realistic sleep occupancy data."""
    
    print(f"Creating {days} days of occupancy data for device {device_id}...")
    
    # Verify device exists
    device = get_device_by_id(device_id)
    if not device:
        print(f"❌ Device {device_id} not found!")
        return 0
    
    print(f"✅ Found device: {device['name']} (ID: {device_id})\n")
    
    now = datetime.now(timezone.utc)
    created_count = 0
    
    for day in range(days):
        day_start = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Randomize sleep schedule slightly
        sleep_start_hour = 23 + random.randint(-1, 1)  # 22:00 - 00:00
        sleep_end_hour = 7 + random.randint(-1, 1)     # 06:00 - 08:00
        
        # Add occasional night wakings
        night_wakings = []
        if random.random() < 0.3:  # 30% chance
            waking_hour = random.randint(1, 5)
            waking_duration = random.randint(5, 30)
            night_wakings.append((waking_hour, waking_duration))
        
        # Create readings every 5 minutes
        for minute in range(0, 1440, 5):
            timestamp = day_start + timedelta(minutes=minute)
            hour = timestamp.hour
            
            # Determine if occupied
            is_occupied = False
            
            if sleep_start_hour >= 23:
                if hour >= sleep_start_hour or hour < sleep_end_hour:
                    is_occupied = True
            else:
                if sleep_start_hour <= hour < sleep_end_hour:
                    is_occupied = True
            
            # Apply night wakings
            for waking_hour, waking_duration in night_wakings:
                waking_start = day_start + timedelta(hours=waking_hour)
                waking_end = waking_start + timedelta(minutes=waking_duration)
                if waking_start <= timestamp < waking_end:
                    is_occupied = False
            
            try:
                reading = create_raw_occupancy(
                    device_id=device_id,
                    occupied=is_occupied,
                    created_at=timestamp.isoformat()
                )
                
                if reading:
                    created_count += 1
                    if created_count % 500 == 0:
                        print(f"   Created {created_count} readings...")
                        
            except Exception as e:
                print(f"❌ Error creating reading: {e}")
                continue
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created_count} occupancy readings")
    print(f"   Device: {device['name']} (ID: {device_id})")
    print(f"   Period: {days} days")
    print(f"   Expected sleep sessions: ~{days} nights")
    print(f"{'='*60}\n")
    
    print("Now run:")
    print(f"  python calculate_dashboard.py {device_id}")
    
    return created_count


if __name__ == "__main__":
    # Use device ID from command line or default
    device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    create_realistic_occupancy(device_id, days)