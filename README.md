# Somnomat Webservice API Documentation

## Base URL
```
http://127.0.0.1:8000
```

## API Version
All endpoints are prefixed with `/api/v1`

---

## Table of Contents
1. [Health Check](#health-check)
2. [Device Endpoints](#device-endpoints)
3. [Reading Endpoints](#reading-endpoints)
4. [Data Models](#data-models)
5. [Examples](#examples)

---

## Health Check

### GET /health
Check if the service is running.

**Request:**
```bash
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

## Device Endpoints

### 1. Register/Update Device
**POST** `/api/v1/devices/`

Register a new device or update an existing device's information.

**Request Body:**
```json
{
  "device_id": "esp32-a1",
  "name": "Demo Device",
  "boardtype": "ESP32-DevKitC",
  "version": "v1.2.3",
  "version_description": "Initial release with sensors",
  "significance_level": "stable"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| device_id | string | Yes | Unique device identifier (1-64 chars) |
| name | string | No | Human-readable device name (max 128 chars) |
| boardtype | string | No | Board type (max 64 chars) |
| version | string | No | Firmware version (max 64 chars) |
| version_description | string | No | Version details (max 512 chars) |
| significance_level | string | No | e.g., "stable", "beta", "experimental" (max 32 chars) |

**Response:** `201 Created`
```json
{
  "id": 1,
  "device_id": "esp32-a1",
  "name": "Demo Device",
  "boardtype": "ESP32-DevKitC",
  "version": "v1.2.3",
  "version_description": "Initial release with sensors",
  "significance_level": "stable",
  "has_binary": false
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/devices/" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-a1",
    "name": "Demo Device",
    "boardtype": "ESP32-DevKitC",
    "version": "v1.2.3",
    "version_description": "Initial release",
    "significance_level": "stable"
  }'
```

---

### 2. List All Devices
**GET** `/api/v1/devices/`

Retrieve a paginated list of all registered devices.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 100 | Number of items per page (1-1000) |
| offset | integer | 0 | Number of items to skip |

**Request:**
```bash
GET /api/v1/devices/?limit=10&offset=0
```

**Response:** `200 OK`
```json
{
  "total": 3,
  "items": [
    {
      "id": 1,
      "device_id": "esp32-a1",
      "name": "Demo Device",
      "boardtype": "ESP32-DevKitC",
      "version": "v1.2.3",
      "version_description": "Initial release",
      "significance_level": "stable",
      "has_binary": false
    },
    {
      "id": 2,
      "device_id": "esp32-b2",
      "name": "Demo Device 2",
      "boardtype": "ESP32-WROOM-32",
      "version": "v1.3.0",
      "version_description": "Added sensors",
      "significance_level": "beta",
      "has_binary": true
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/devices/?limit=10&offset=0"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/api/v1/devices/",
    params={"limit": 10, "offset": 0}
)
data = response.json()
print(f"Total devices: {data['total']}")
for device in data['items']:
    print(f"- {device['device_id']}: {device['name']}")
```

---

### 3. Upload Binary File
**POST** `/api/v1/devices/{device_id}/binary`

Upload a binary firmware file for a specific device.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| device_id | string | The unique device identifier |

**Request Body:**
- Content-Type: `multipart/form-data`
- Field name: `file`
- File: Binary file (firmware, configuration, etc.)

**Response:** `200 OK`
```json
{
  "message": "Binary file uploaded successfully",
  "device_id": "esp32-a1",
  "file_size": 524288
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/devices/esp32-a1/binary" \
  -F "file=@firmware.bin"
```

**Python Example:**
```python
import requests

with open('firmware.bin', 'rb') as f:
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/devices/esp32-a1/binary",
        files={'file': f}
    )
print(response.json())
```

**Error Responses:**
- `404 Not Found`: Device not found

---

### 4. Download Binary File
**GET** `/api/v1/devices/{device_id}/binary`

Download the binary file associated with a device.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| device_id | string | The unique device identifier |

**Response:** `200 OK`
- Content-Type: `application/octet-stream`
- Body: Binary file content

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/devices/esp32-a1/binary" \
  -o downloaded_firmware.bin
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/api/v1/devices/esp32-a1/binary"
)
with open('downloaded_firmware.bin', 'wb') as f:
    f.write(response.content)
```

**Error Responses:**
- `404 Not Found`: Device not found or no binary file available

---

## Reading Endpoints

### 5. Create Health Reading
**POST** `/api/v1/readings/`

Submit a new health metrics reading for a device. If the device doesn't exist, it will be created automatically.

**Request Body:**
```json
{
  "device_id": "esp32-a1",
  "heartrate": 72.5,
  "hrv": 45.2,
  "time_in_bed": 7.5,
  "total_use_time": 8.2,
  "timestamp": "2024-11-06T10:30:00Z"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| device_id | string | Yes | Unique device identifier (1-64 chars) |
| heartrate | float | No | Heart rate in beats per minute (≥0) |
| hrv | float | No | Heart Rate Variability in milliseconds (≥0) |
| time_in_bed | float | No | Time in bed in hours (≥0) |
| total_use_time | float | No | Total device use time in hours (≥0) |
| timestamp | datetime | No | ISO-8601 UTC timestamp (defaults to server time) |

**Response:** `201 Created`
```json
{
  "id": 1,
  "device_id": 1,
  "timestamp": "2024-11-06T10:30:00Z",
  "heartrate": 72.5,
  "hrv": 45.2,
  "time_in_bed": 7.5,
  "total_use_time": 8.2
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/readings/" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-a1",
    "heartrate": 72.5,
    "hrv": 45.2,
    "time_in_bed": 7.5,
    "total_use_time": 8.2
  }'
```

**Python Example:**
```python
import requests
from datetime import datetime, timezone

reading = {
    "device_id": "esp32-a1",
    "heartrate": 72.5,
    "hrv": 45.2,
    "time_in_bed": 7.5,
    "total_use_time": 8.2,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

response = requests.post(
    "http://127.0.0.1:8000/api/v1/readings/",
    json=reading
)
print(response.json())
```

---

### 6. List Readings
**GET** `/api/v1/readings/`

Retrieve health readings with optional filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device_id | string | None | Filter by device ID |
| limit | integer | 100 | Number of items per page (1-1000) |
| offset | integer | 0 | Number of items to skip |
| since | datetime | None | Filter readings after this time (ISO-8601 UTC) |
| until | datetime | None | Filter readings before this time (ISO-8601 UTC) |

**Request:**
```bash
GET /api/v1/readings/?device_id=esp32-a1&limit=10&offset=0
```

**Response:** `200 OK`
```json
{
  "total": 300,
  "items": [
    {
      "id": 1,
      "device_id": "esp32-a1",
      "timestamp": "2024-11-06T10:30:00Z",
      "heartrate": 72.5,
      "hrv": 45.2,
      "time_in_bed": 7.5,
      "total_use_time": 8.2
    },
    {
      "id": 2,
      "device_id": "esp32-a1",
      "timestamp": "2024-11-06T10:25:00Z",
      "heartrate": 68.3,
      "hrv": 42.1,
      "time_in_bed": 7.2,
      "total_use_time": 8.0
    }
  ]
}
```

**cURL Examples:**

All readings (paginated):
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/readings/?limit=10&offset=0"
```

Filter by device:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/readings/?device_id=esp32-a1&limit=10"
```

Filter by time range:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/readings/?since=2024-11-06T00:00:00Z&until=2024-11-06T23:59:59Z"
```

**Python Examples:**

Fetch all readings for a device:
```python
import requests

def fetch_all_readings(device_id):
    all_items = []
    offset = 0
    limit = 1000
    
    while True:
        response = requests.get(
            "http://127.0.0.1:8000/api/v1/readings/",
            params={
                "device_id": device_id,
                "limit": limit,
                "offset": offset
            }
        )
        data = response.json()
        all_items.extend(data['items'])
        
        if offset + len(data['items']) >= data['total']:
            break
        offset += limit
    
    return all_items

readings = fetch_all_readings("esp32-a1")
print(f"Total: {len(readings)} readings")
```

Filter by time range:
```python
import requests
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
one_day_ago = now - timedelta(days=1)

response = requests.get(
    "http://127.0.0.1:8000/api/v1/readings/",
    params={
        "device_id": "esp32-a1",
        "since": one_day_ago.isoformat(),
        "until": now.isoformat(),
        "limit": 100
    }
)
data = response.json()
print(f"Readings in last 24h: {data['total']}")
```

---

## Data Models

### Device Model
```json
{
  "id": 1,
  "device_id": "esp32-a1",
  "name": "Demo Device",
  "boardtype": "ESP32-DevKitC",
  "version": "v1.2.3",
  "version_description": "Initial release",
  "significance_level": "stable",
  "has_binary": false
}
```

### Reading Model
```json
{
  "id": 1,
  "device_id": "esp32-a1",
  "timestamp": "2024-11-06T10:30:00Z",
  "heartrate": 72.5,
  "hrv": 45.2,
  "time_in_bed": 7.5,
  "total_use_time": 8.2
}
```

### Paginated Response Model
```json
{
  "total": 300,
  "items": [...]
}
```

---

## Examples

### Complete Python Client Example

```python
import requests
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000/api/v1"

class SomnomatClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    # Device Operations
    def register_device(self, device_id, name=None, boardtype=None, 
                       version=None, description=None, level=None):
        """Register or update a device."""
        data = {"device_id": device_id}
        if name: data["name"] = name
        if boardtype: data["boardtype"] = boardtype
        if version: data["version"] = version
        if description: data["version_description"] = description
        if level: data["significance_level"] = level
        
        response = requests.post(f"{self.base_url}/devices/", json=data)
        response.raise_for_status()
        return response.json()
    
    def list_devices(self, limit=100, offset=0):
        """List all devices."""
        response = requests.get(
            f"{self.base_url}/devices/",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_binary(self, device_id, file_path):
        """Upload a binary file for a device."""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/devices/{device_id}/binary",
                files={'file': f}
            )
        response.raise_for_status()
        return response.json()
    
    def download_binary(self, device_id, output_path):
        """Download binary file for a device."""
        response = requests.get(
            f"{self.base_url}/devices/{device_id}/binary"
        )
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path
    
    # Reading Operations
    def create_reading(self, device_id, heartrate=None, hrv=None,
                      time_in_bed=None, total_use_time=None, timestamp=None):
        """Create a new health reading."""
        data = {"device_id": device_id}
        if heartrate is not None: data["heartrate"] = heartrate
        if hrv is not None: data["hrv"] = hrv
        if time_in_bed is not None: data["time_in_bed"] = time_in_bed
        if total_use_time is not None: data["total_use_time"] = total_use_time
        if timestamp: data["timestamp"] = timestamp
        
        response = requests.post(f"{self.base_url}/readings/", json=data)
        response.raise_for_status()
        return response.json()
    
    def list_readings(self, device_id=None, limit=100, offset=0,
                     since=None, until=None):
        """List readings with optional filters."""
        params = {"limit": limit, "offset": offset}
        if device_id: params["device_id"] = device_id
        if since: params["since"] = since
        if until: params["until"] = until
        
        response = requests.get(f"{self.base_url}/readings/", params=params)
        response.raise_for_status()
        return response.json()
    
    def fetch_all_readings(self, device_id):
        """Fetch all readings for a device (handles pagination)."""
        all_items = []
        offset = 0
        limit = 1000
        
        while True:
            data = self.list_readings(
                device_id=device_id,
                limit=limit,
                offset=offset
            )
            all_items.extend(data['items'])
            
            if offset + len(data['items']) >= data['total']:
                break
            offset += limit
        
        return all_items

# Usage Example
if __name__ == "__main__":
    client = SomnomatClient()
    
    # Register a device
    device = client.register_device(
        device_id="esp32-test",
        name="Test Device",
        boardtype="ESP32-DevKitC",
        version="v1.0.0"
    )
    print(f"Registered device: {device['device_id']}")
    
    # Submit a reading
    reading = client.create_reading(
        device_id="esp32-test",
        heartrate=75.0,
        hrv=50.0,
        time_in_bed=8.0,
        total_use_time=9.0
    )
    print(f"Created reading: {reading['id']}")
    
    # Fetch all readings
    readings = client.fetch_all_readings("esp32-test")
    print(f"Total readings: {len(readings)}")
```

### ESP32 Arduino Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "your-wifi-ssid";
const char* password = "your-wifi-password";
const char* serverUrl = "http://192.168.1.100:8000/api/v1";
const char* deviceId = "esp32-bedroom";

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  
  // Register device
  registerDevice();
}

void loop() {
  // Read sensor data (example values)
  float heartrate = readHeartRate();
  float hrv = readHRV();
  float timeInBed = 7.5;
  float totalUseTime = 8.0;
  
  // Send reading
  sendReading(heartrate, hrv, timeInBed, totalUseTime);
  
  delay(300000); // Send every 5 minutes
}

void registerDevice() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "/devices/";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    StaticJsonDocument<200> doc;
    doc["device_id"] = deviceId;
    doc["name"] = "Bedroom Monitor";
    doc["boardtype"] = "ESP32-DevKitC";
    doc["version"] = "v1.0.0";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    if (httpCode > 0) {
      Serial.printf("Device registered: %d\n", httpCode);
    }
    http.end();
  }
}

void sendReading(float hr, float hrv, float bed, float use) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "/readings/";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    StaticJsonDocument<300> doc;
    doc["device_id"] = deviceId;
    doc["heartrate"] = hr;
    doc["hrv"] = hrv;
    doc["time_in_bed"] = bed;
    doc["total_use_time"] = use;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    if (httpCode > 0) {
      Serial.printf("Reading sent: %d\n", httpCode);
    }
    http.end();
  }
}

float readHeartRate() {
  // Implement your heart rate sensor reading
  return 72.5;
}

float readHRV() {
  // Implement your HRV calculation
  return 45.0;
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
Invalid request parameters or body.

```json
{
  "detail": "Invalid input data"
}
```

### 404 Not Found
Resource not found (device or binary file).

```json
{
  "detail": "Device esp32-xyz not found"
}
```

### 422 Unprocessable Entity
Validation error.

```json
{
  "detail": [
    {
      "loc": ["body", "heartrate"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### 500 Internal Server Error
Server error.

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. For production deployment, consider implementing rate limiting.

---

## Authentication

Currently, the API does not require authentication. For production deployment, implement API keys or OAuth2.

---

## CORS Configuration

CORS is configured via the `ALLOWED_ORIGINS` environment variable in [.env](somnomat_webservice/.env).

Example:
```
ALLOWED_ORIGINS=http://localhost:3000,https://myapp.com
```

---

## Database

- **Type**: SQLite (default) or PostgreSQL/MySQL
- **Location**: `data.db` in the application root
- **Schema**: See [models.py](somnomat_webservice/app/models.py)

---

## Running the Server

```bash
# Navigate to project directory
cd somnomat_webservice

# Activate virtual environment
source ../.webservice/bin/activate

# Run the server
python -m uvicorn app.main:app --reload

# Server runs at http://127.0.0.1:8000
```

---

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

These interfaces allow you to test all endpoints directly from your browser.

---

## Version History

- **v0.1.0** - Initial release with device management and health metrics tracking
