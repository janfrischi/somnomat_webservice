from pydantic import BaseModel, Field
from datetime import datetime

# API Data Validation Schemas -> Pydantic models to validate request and response data
# Defines schemas for creating readings and outputting data

# ----- Devices -----
class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=128)

class DeviceOut(BaseModel):
    id: int
    device_id: str
    name: str | None

    class Config:
        from_attributes = True

# ----- Readings -----
class ReadingCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    sensor: str = Field(min_length=1, max_length=64)
    value: float
    timestamp: datetime | None = None  # optional client-provided time (UTC)

class ReadingOut(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    sensor: str
    value: float

    class Config:
        from_attributes = True

# ----- Common -----
class Paginated(BaseModel):
    total: int
    items: list
