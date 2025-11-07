import requests

r = requests.get("http://127.0.0.1:8000/api/v1/readings", params={
    "device_id": "esp32-a1",
    "limit": 10
})
data = r.json()
print(f"Total readings: {data['total']}\n")
for reading in data['items']:
    print(f"Timestamp: {reading['timestamp']}")
    print(f"  Heartrate: {reading['heartrate']} bpm")
    print(f"  HRV: {reading['hrv']} ms")
    print(f"  Time in bed: {reading['time_in_bed']} h")
    print(f"  Total use time: {reading['total_use_time']} h")
    print()
