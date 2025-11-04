# This file defines database schema and object-relational mappings (ORM) for the application.
# Each class (Device and Reading) corresponds to a database table.

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from app.database import Base

# Define Device Table
class Device(Base):
    # Define table name
    __tablename__ = "devices"
    # Define columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Unique device identifier
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Define relationships with the readings table, cascade on delete
    readings: Mapped[list["Reading"]] = relationship(
    back_populates="device", cascade="all, delete-orphan"
)

# Define Reading Table    
class Reading(Base):
    __tablename__ = "readings"
    # Define columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Foreign key to the devices table
    device_id: Mapped[int] = mapped_column(
    ForeignKey("devices.id", ondelete="CASCADE"), index=True
)
    # Store when the reading was taken
    timestamp: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), index=True
)
    # Sensor type
    sensor: Mapped[str] = mapped_column(String(64), index=True)
    # Numeric reading
    value: Mapped[float] = mapped_column(Float)

    device: Mapped["Device"] = relationship(back_populates="readings")






