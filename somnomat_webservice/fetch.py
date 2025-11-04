import requests

r = requests.get("http://127.0.0.1:8000/api/v1/readings", params={
    "device_id": "esp32-a1",
    "sensor": "temperature",
    "limit": 10
})
print(r.json())
