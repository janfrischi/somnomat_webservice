from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/", response_model=schemas.DeviceOut, status_code=201)
def register_device(payload: schemas.DeviceCreate, db: Session = Depends(get_db)):
    device = crud.get_or_create_device(db, device_id=payload.device_id, name=payload.name)
    return device

@router.get("/", response_model=schemas.Paginated)
def get_devices(db: Session = Depends(get_db), limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    total, items = crud.list_devices(db, limit=limit, offset=offset)
    
    # Convert ORM objects to dictionaries
    formatted_items = [
        {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name
        }
        for device in items
    ]
    
    return {"total": total, "items": formatted_items}
