"""Test script for the new Supabase API client."""
from supabase_api_client_somnomat import *
from datetime import datetime, timedelta, timezone
import random

print("=" * 60)
print("Testing New Supabase API Client")
print("=" * 60)

# Test 1: Create a device
print("\n1. Creating a new device...")
device = create_device(
    name="Test Device",
    boardtype=1,
    mac="AA:BB:CC:DD:EE:FF",
    hardware_version="1.0"
)

if device:
    device_id = device['id']
    print(f"✅ Device created with ID: {device_id}")
    print(f"   Name: {device['name']}")
    print(f"   Board Type: {device['boardtype']}")
    print(f"   MAC: {device['mac']}")
else:
    print("❌ Failed to create device")
    exit(1)

# Test 2: Create firmware entry
print(f"\n2. Creating firmware for device {device_id}...")
firmware = create_firmware(
    version="1.0.0",
    significance_level=1,
    partition=0,
    device_id=device_id
)

if firmware:
    print(f"✅ Firmware created with ID: {firmware['id']}")
    print(f"   Version: {firmware['version']}")

# Test 3: Create user settings
print(f"\n3. Creating user settings for device {device_id}...")
settings = create_user_settings(
    device_id=device_id,
    amplitude=50,
    frequency=10,
    vibration=3
)

if settings:
    print(f"✅ Settings created with ID: {settings['id']}")
    print(f"   Amplitude: {settings['amplitude']}")
    print(f"   Frequency: {settings['frequency']}")

# Test 4: Create raw occupancy readings for a full week (5-minute intervals)
print(f"\n4. Creating occupancy readings for one week (5-min intervals)...")
print(f"   Generating realistic sleep patterns...")

# Generate readings for 7 days
readings = []
now = datetime.now(timezone.utc)
start_time = now - timedelta(days=7)  # Start from 7 days ago

# 5-minute intervals for 7 days = 7 * 24 * 60 / 5 = 2016 readings
interval_minutes = 5
total_minutes = 7 * 24 * 60
num_readings = total_minutes // interval_minutes

for i in range(num_readings):
    timestamp = start_time + timedelta(minutes=i * interval_minutes)
    
    # Simulate realistic sleep pattern:
    # - Sleep from ~22:00 to ~06:00 (occupied = True)
    # - Awake during the day (occupied = False)
    # - Add some randomness for realism
    hour = timestamp.hour
    
    if 22 <= hour or hour < 6:
        # Night time - mostly occupied
        occupied = random.random() < 0.95  # 95% occupied during sleep hours
    elif 6 <= hour < 8:
        # Morning transition - 50/50
        occupied = random.random() < 0.5
    elif 8 <= hour < 22:
        # Day time - mostly not occupied
        occupied = random.random() < 0.1  # 10% occupied during day
    else:
        occupied = False
    
    readings.append({
        "occupied": occupied,
        "created_at": timestamp.isoformat()
    })

print(f"   Generated {len(readings)} readings")
print(f"   Time range: {readings[0]['created_at']} to {readings[-1]['created_at']}")

# Insert in batches of 1000 (Supabase limit)
batch_size = 1000
total_inserted = 0

for i in range(0, len(readings), batch_size):
    batch = readings[i:i + batch_size]
    result = create_bulk_raw_occupancy(device_id, batch)
    total_inserted += len(result)
    print(f"   Inserted batch {i//batch_size + 1}: {len(result)} readings")

print(f"✅ Total occupancy readings created: {total_inserted}")

# Test 5: Get current occupancy status
print(f"\n5. Getting current occupancy status...")
current = get_current_occupancy_status(device_id)
print(f"✅ Current status: {'Occupied' if current else 'Vacant'}")

# Test 6: Create dashboard with ALL columns populated
print(f"\n6. Creating dashboard for device {device_id}...")
dashboard = create_or_update_dashboard(
    device_id=device_id,
    # Metrics (float columns)
    sleep_consistency=85.5,
    bedtime_consistency=90.0,
    bed_use=28.5,
    daily_occupancy=7.2,
    total_intervals=12.0,
    total_nights=30.0,
    avg_sleep_per_night=7.5,
    # Suggestion columns (text)
    suggestion_awakening="Great job! You're sleeping through the night with minimal interruptions.",
    suggestion_avg_sleep="Excellent! You're getting the recommended 7-9 hours of sleep.",
    suggestion_consistency="Excellent sleep consistency! Keep maintaining your regular sleep schedule.",
    suggestion_bed_use="Your bed usage time is appropriate for healthy sleep patterns."
)

if dashboard:
    print(f"✅ Dashboard created with ALL columns populated")
    print(f"\n   📊 Metrics:")
    print(f"      Sleep Consistency: {dashboard['sleep_consistency']}/100")
    print(f"      Bedtime Consistency: {dashboard['bedtime_consistency']}/100")
    print(f"      Bed Use: {dashboard['bed_use']}%")
    print(f"      Daily Occupancy: {dashboard['daily_occupancy']} hrs/day")
    print(f"      Total Intervals: {dashboard['total_intervals']}")
    print(f"      Total Nights: {dashboard['total_nights']}")
    print(f"      Avg Sleep: {dashboard['avg_sleep_per_night']} hrs/night")
    print(f"\n   💡 Suggestions:")
    print(f"      Awakening: {dashboard['suggestion_awakening'][:50]}...")
    print(f"      Avg Sleep: {dashboard['suggestion_avg_sleep'][:50]}...")
    print(f"      Consistency: {dashboard['suggestion_consistency'][:50]}...")
    print(f"      Bed Use: {dashboard['suggestion_bed_use'][:50]}...")
else:
    print("❌ Failed to create dashboard")

# Test 7: Get device with all data
print(f"\n7. Getting device with all related data...")
full_device = get_device_with_all_data(device_id)
if full_device:
    print(f"✅ Retrieved complete device data")
    print(f"   Firmware entries: {len(full_device['firmware'])}")
    print(f"   Has settings: {full_device['settings'] is not None}")
    print(f"   Has dashboard: {full_device['dashboard'] is not None}")
    print(f"   Current occupancy: {full_device['current_occupancy']}")

# Test 8: Verify occupancy data was created
print(f"\n8. Verifying occupancy data...")
occupancy_count = len(get_raw_occupancy_by_device(device_id, limit=5000))
print(f"✅ Total occupancy readings in database: {occupancy_count}")

print("\n" + "=" * 60)
print("🎉 All tests completed!")
print("=" * 60)