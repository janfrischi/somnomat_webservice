import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

def fetch_all_device_data(device_id: str):
    """Fetch all readings for a device with automatic pagination."""
    all_items = []
    offset = 0
    limit = 1000
    
    while True:
        params = {
            "device_id": device_id,
            "limit": limit,
            "offset": offset
        }
        response = requests.get(f"{BASE_URL}/readings", params=params)
        response.raise_for_status()
        data = response.json()
        
        all_items.extend(data['items'])
        print(f"Progress: {len(all_items)}/{data['total']}")
        
        if offset + len(data['items']) >= data['total']:
            break
        
        offset += limit
    
    return all_items

# Get all readings for esp32-a1
all_readings = fetch_all_device_data("esp32-a1")
print(f"\nTotal readings: {len(all_readings)}")

# Calculate averages
if all_readings:
    avg_heartrate = sum(r['heartrate'] for r in all_readings if r['heartrate']) / len([r for r in all_readings if r['heartrate']])
    avg_hrv = sum(r['hrv'] for r in all_readings if r['hrv']) / len([r for r in all_readings if r['hrv']])
    avg_time_in_bed = sum(r['time_in_bed'] for r in all_readings if r['time_in_bed']) / len([r for r in all_readings if r['time_in_bed']])
    
    print(f"\nAverage metrics:")
    print(f"  - Heartrate: {avg_heartrate:.1f} bpm")
    print(f"  - HRV: {avg_hrv:.1f} ms")
    print(f"  - Time in bed: {avg_time_in_bed:.1f} h")

# Show latest 5
print("\nLatest 5 readings:")
for r in all_readings[:5]:
    print(f"{r['timestamp']}: HR={r['heartrate']:.1f} bpm, HRV={r['hrv']:.1f} ms, Bed={r['time_in_bed']:.1f}h")