# Data access layer that contains business logic functions -> Connects API to the database using SQLAlchemy
from sqlalchemy.orm import Session
# SQL core queries 
from sqlalchemy import select, func
from datetime import datetime
from app import models, schemas


# Find existing device or create a new one
def get_or_create_device(db: Session, device_id: str, name: str | None = None) -> models.Device:
    device = db.execute(select(models.Device).where(models.Device.device_id == device_id)).scalar_one_or_none()
    if device:
        # Update name if provided and changed
        if name is not None and device.name != name:
            device.name = name
            db.add(device)
            db.commit()
            db.refresh(device)
        return device
    device = models.Device(device_id=device_id, name=name)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

# Create a new sensor reading
def create_reading(db: Session, payload: schemas.ReadingCreate) -> models.Reading:
    device = get_or_create_device(db, device_id=payload.device_id)
    ts = payload.timestamp or datetime.utcnow()
    reading = models.Reading(device_id=device.id, sensor=payload.sensor, value=payload.value, timestamp=ts)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading

# Queries sensor readings with optional filters
def list_readings(
    db: Session,
    device_id: str | None = None,
    sensor: str | None = None,
    limit: int = 100,
    offset: int = 0,
    since: datetime | None = None,
    until: datetime | None = None,
):
    stmt = select(models.Reading)
    if device_id:
        dev = db.execute(select(models.Device).where(models.Device.device_id == device_id)).scalar_one_or_none()
        if dev:
            stmt = stmt.where(models.Reading.device_id == dev.id)
        else:
            return 0, []
    if sensor:
        stmt = stmt.where(models.Reading.sensor == sensor)
    if since:
        stmt = stmt.where(models.Reading.timestamp >= since)
    if until:
        stmt = stmt.where(models.Reading.timestamp <= until)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(models.Reading.timestamp.desc()).limit(limit).offset(offset)).scalars().all()
    return total, items

# List all devices with pagination
def list_devices(db: Session, limit: int = 100, offset: int = 0):
    stmt = select(models.Device).order_by(models.Device.id.asc()).limit(limit).offset(offset)
    total = db.execute(select(func.count()).select_from(models.Device)).scalar_one()
    items = db.execute(stmt).scalars().all()
    return total, items