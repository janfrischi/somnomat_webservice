from pydantic import BaseModel, Field
from datetime import datetime

# API Data Validation Schemas -> Pydantic models to validate request and response data
# Defines schemas for creating readings and outputting data

# ----- Devices -----
class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    boardtype: str | None = Field(default=None, max_length=64)
    version: str | None = Field(default=None, max_length=64)
    version_description: str | None = Field(default=None, max_length=512)
    significance_level: str | None = Field(default=None, max_length=32)

class DeviceOut(BaseModel):
    id: int
    device_id: str
    name: str | None
    boardtype: str | None
    version: str | None
    version_description: str | None
    significance_level: str | None
    has_binary: bool = Field(default=False, description="Whether a binary file is attached")

    class Config:
        from_attributes = True

# ----- Readings -----
class ReadingCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    heartrate: float | None = Field(default=None, ge=0, description="Heart rate in bpm")
    hrv: float | None = Field(default=None, ge=0, description="Heart Rate Variability in ms")
    time_in_bed: float | None = Field(default=None, ge=0, description="Time in bed in hours")
    total_use_time: float | None = Field(default=None, ge=0, description="Total device use time in hours")
    timestamp: datetime | None = None  # optional client-provided time (UTC)

class ReadingOut(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    heartrate: float | None
    hrv: float | None
    time_in_bed: float | None
    total_use_time: float | None

    class Config:
        from_attributes = True

# ----- Common -----
class Paginated(BaseModel):
    total: int
    items: list
