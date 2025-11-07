import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.crud import get_or_create_device, create_reading
from app.schemas import ReadingCreate

Base.metadata.create_all(bind=engine)

def run():
    db: Session = SessionLocal()
    try:
        # Define device configurations with all new fields
        device_configs = [
            {
                "device_id": "esp32-a1",
                "name": "Demo esp32-a1",
                "boardtype": "ESP32-DevKitC",
                "version": "v1.2.3",
                "version_description": "Initial release with temperature and humidity sensors",
                "significance_level": "stable"
            },
            {
                "device_id": "esp32-b2",
                "name": "Demo esp32-b2",
                "boardtype": "ESP32-WROOM-32",
                "version": "v1.3.0",
                "version_description": "Added pressure sensor support and improved WiFi stability",
                "significance_level": "beta"
            },
            {
                "device_id": "esp32-c3",
                "name": "Demo esp32-c3",
                "boardtype": "ESP32-C3-Mini",
                "version": "v2.0.0-rc1",
                "version_description": "Major update with new power management features",
                "significance_level": "experimental"
            }
        ]
        
        now = datetime.now(timezone.utc)
        
        for dev_config in device_configs:
            # Create device with all fields populated
            get_or_create_device(
                db, 
                device_id=dev_config["device_id"],
                name=dev_config["name"],
                boardtype=dev_config["boardtype"],
                version=dev_config["version"],
                version_description=dev_config["version_description"],
                significance_level=dev_config["significance_level"]
            )
            
            # Create realistic health metrics readings
            for i in range(300):  # 300 points/device
                ts = now - timedelta(minutes=5*i)
                
                # Generate realistic health metrics
                heartrate = 60 + random.uniform(-10, 30)  # 50-90 bpm
                hrv = 30 + random.uniform(-10, 40)  # 20-70 ms
                time_in_bed = 7 + random.uniform(-1, 2)  # 6-9 hours
                total_use_time = 8 + random.uniform(-2, 4)  # 6-12 hours
                
                create_reading(
                    db, 
                    ReadingCreate(
                        device_id=dev_config["device_id"],
                        heartrate=heartrate,
                        hrv=hrv,
                        time_in_bed=time_in_bed,
                        total_use_time=total_use_time,
                        timestamp=ts
                    )
                )
        
        print("✅ Seeded dummy data with health metrics.")
        print(f"   - Created {len(device_configs)} devices")
        print(f"   - Created {len(device_configs) * 300} readings")
        print(f"   - Metrics: heartrate, hrv, time_in_bed, total_use_time")
        
    finally:
        db.close()

if __name__ == "__main__":
    run()