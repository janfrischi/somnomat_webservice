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
        devices = ["esp32-a1", "esp32-b2", "esp32-c3"]
        sensors = ["temperature", "humidity", "pressure"]
        now = datetime.now(timezone.utc)
        for dev in devices:
            get_or_create_device(db, device_id=dev, name=f"Demo {dev}")
            for i in range(300):  # 300 points/device
                ts = now - timedelta(minutes=5*i)
                sensor = random.choice(sensors)
                base = {"temperature": 22.0, "humidity": 45.0, "pressure": 1013.0}[sensor]
                val = base + random.uniform(-2.5, 2.5)
                create_reading(db, ReadingCreate(device_id=dev, sensor=sensor, value=val, timestamp=ts))
        print("Seeded dummy data.")
    finally:
        db.close()

if __name__ == "__main__":
    run()