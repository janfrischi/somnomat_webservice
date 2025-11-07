from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/", response_model=schemas.DeviceOut, status_code=201)
def register_device(payload: schemas.DeviceCreate, db: Session = Depends(get_db)):
    device = crud.get_or_create_device(
        db, 
        device_id=payload.device_id, 
        name=payload.name,
        boardtype=payload.boardtype,
        version=payload.version,
        version_description=payload.version_description,
        significance_level=payload.significance_level
    )
    return {
        "id": device.id,
        "device_id": device.device_id,
        "name": device.name,
        "boardtype": device.boardtype,
        "version": device.version,
        "version_description": device.version_description,
        "significance_level": device.significance_level,
        "has_binary": device.binary_file is not None
    }

@router.get("/", response_model=schemas.Paginated)
def get_devices(db: Session = Depends(get_db), limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    total, items = crud.list_devices(db, limit=limit, offset=offset)
    
    # Convert ORM objects to dictionaries
    formatted_items = [
        {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name,
            "boardtype": device.boardtype,
            "version": device.version,
            "version_description": device.version_description,
            "significance_level": device.significance_level,
            "has_binary": device.binary_file is not None
        }
        for device in items
    ]
    
    return {"total": total, "items": formatted_items}

@router.post("/{device_id}/binary", status_code=200)
async def upload_binary(
    device_id: str, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """Upload a binary file for a device."""
    try:
        binary_data = await file.read()
        device = crud.update_device_binary(db, device_id, binary_data)
        return {
            "message": "Binary file uploaded successfully",
            "device_id": device.device_id,
            "file_size": len(binary_data)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/binary")
def download_binary(device_id: str, db: Session = Depends(get_db)):
    """Download the binary file for a device."""
    try:
        binary_data = crud.get_device_binary(db, device_id)
        if binary_data is None:
            raise HTTPException(status_code=404, detail="No binary file found for this device")
        return Response(content=binary_data, media_type="application/octet-stream")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
