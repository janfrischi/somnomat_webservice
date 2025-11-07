from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import schemas, crud, models

# Create a router object with a prefix /readings
router = APIRouter(
    prefix="/readings",
    tags=["readings"]
)

# POST /api/v1/readings -> Add a new reading
@router.post("/", response_model=schemas.ReadingOut, status_code=201)
def ingest_reading(payload: schemas.ReadingCreate, db: Session = Depends(get_db)):
    """Ingest one health metrics reading. Create the device on the fly if missing."""
    return crud.create_reading(db, payload)

# GET /api/v1/readings -> Fetch readings
@router.get("/", response_model=schemas.Paginated)
def get_readings(
    db: Session = Depends(get_db),
    device_id: str | None = Query(None, description="Public device_id string"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    since: datetime | None = Query(None, description="ISO-8601 UTC"),
    until: datetime | None = Query(None, description="ISO-8601 UTC"),
):
    total, items = crud.list_readings(
        db,
        device_id=device_id,
        limit=limit,
        offset=offset,
        since=since,
        until=until
    )
    
    # Convert ORM objects to dictionaries with proper device_id
    formatted_items = []
    for reading in items:
        # Get the device to retrieve the public device_id string
        device = db.query(models.Device).filter(
            models.Device.id == reading.device_id
        ).first()
        
        formatted_items.append({
            "id": reading.id,
            "device_id": device.device_id if device else "unknown",
            "heartrate": reading.heartrate,
            "hrv": reading.hrv,
            "time_in_bed": reading.time_in_bed,
            "total_use_time": reading.total_use_time,
            "timestamp": reading.timestamp.isoformat()
        })
    
    return {"total": total, "items": formatted_items}
