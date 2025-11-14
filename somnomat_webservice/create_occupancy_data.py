"""Create realistic occupancy data for testing the dashboard."""
from supabase_api_client_somnomat import create_raw_occupancy, get_device_by_id
from datetime import datetime, timedelta, timezone

# Use device ID from command line or default
import sys
device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 17

print(f"Creating occupancy data for device {device_id}...")

# Verify device exists
device = get_device_by_id(device_id)
if not device:
    print(f"❌ Device {device_id} not found!")
    exit(1)

print(f"✅ Found device: {device['name']} (ID: {device_id})\n")

# Generate 7 days of realistic sleep data
now = datetime.now(timezone.utc)
created_count = 0

for day in range(7):
    day_start = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create readings every 30 minutes (48 readings per day)
    for half_hour in range(48):
        timestamp = day_start + timedelta(minutes=half_hour * 30)
        hour = timestamp.hour
        
        # Sleep pattern: occupied from 11 PM (23:00) to 7 AM (07:00)
        # That's 8 hours of sleep
        is_occupied = hour >= 23 or hour < 7
        
        try:
            reading = create_raw_occupancy(
                device_id=device_id,
                occupied=is_occupied,
                created_at=timestamp.isoformat()  # ✅ Pass the historical timestamp!
            )
            
            if reading:
                created_count += 1
                if created_count % 50 == 0:  # Print progress every 50 readings
                    print(f"   Created {created_count} readings...")
        except Exception as e:
            print(f"❌ Error creating reading: {e}")
            break

print(f"\n{'='*60}")
print(f"✅ Successfully created {created_count} occupancy readings")
print(f"   Device: {device['name']} (ID: {device_id})")
print(f"   Period: {7} days")
print(f"   Expected sleep sessions: ~7 nights")
print(f"{'='*60}\n")

print("Now run:")
print(f"  python calculate_dashboard.py {device_id}")