import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"  # Your local server

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

# Filter by sensor type
temperature_readings = [r for r in all_readings if r['sensor'] == 'temperature']
print(f"Temperature readings: {len(temperature_readings)}")

# Show latest 10
print("\nLatest 10 readings:")
for r in all_readings[:10]:
    print(f"{r['timestamp']}: {r['sensor']} = {r['value']}")