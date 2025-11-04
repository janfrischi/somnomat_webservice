import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_readings_endpoint():
    """Test the readings endpoint with various filters."""
    
    print("=" * 60)
    print("Testing Readings Endpoint")
    print("=" * 60)
    
    # Test 1: Get all readings (limited)
    print("\n1. Getting all readings (limit 5)...")
    response = requests.get(f"{BASE_URL}/readings/", params={"limit": 5})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Returned: {len(data['items'])} items")
        if data['items']:
            print(f"   First item: {data['items'][0]}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 2: Filter by device
    print("\n2. Getting readings for esp32-a1...")
    response = requests.get(f"{BASE_URL}/readings/", params={
        "device_id": "esp32-a1",
        "limit": 5
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Returned: {len(data['items'])} items")
        if data['items']:
            print(f"   Device IDs: {set(item['device_id'] for item in data['items'])}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 3: Filter by sensor
    print("\n3. Getting temperature readings...")
    response = requests.get(f"{BASE_URL}/readings/", params={
        "sensor": "temperature",
        "limit": 5
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Returned: {len(data['items'])} items")
        if data['items']:
            print(f"   Sensors: {set(item['sensor'] for item in data['items'])}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 4: Combined filters
    print("\n4. Getting temperature readings for esp32-a1...")
    response = requests.get(f"{BASE_URL}/readings/", params={
        "device_id": "esp32-a1",
        "sensor": "temperature",
        "limit": 5
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Returned: {len(data['items'])} items")
    else:
        print(f"   Error: {response.text}")
    
    # Test 5: Time range filter
    print("\n5. Getting recent readings (last hour)...")
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    response = requests.get(f"{BASE_URL}/readings/", params={
        "since": one_hour_ago.isoformat(),
        "limit": 5
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Returned: {len(data['items'])} items")
    else:
        print(f"   Error: {response.text}")
    
    # Test 6: Pagination
    print("\n6. Testing pagination...")
    response1 = requests.get(f"{BASE_URL}/readings/", params={
        "device_id": "esp32-a1",
        "limit": 10,
        "offset": 0
    })
    response2 = requests.get(f"{BASE_URL}/readings/", params={
        "device_id": "esp32-a1",
        "limit": 10,
        "offset": 10
    })
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        print(f"   Page 1: {len(data1['items'])} items")
        print(f"   Page 2: {len(data2['items'])} items")
        print(f"   Total: {data1['total']}")
        # Check no overlap
        ids1 = {item['id'] for item in data1['items']}
        ids2 = {item['id'] for item in data2['items']}
        print(f"   No overlap: {len(ids1.intersection(ids2)) == 0}")
    else:
        print(f"   Error in pagination test")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_readings_endpoint()