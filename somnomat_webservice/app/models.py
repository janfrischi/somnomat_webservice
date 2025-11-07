# This file defines database schema and object-relational mappings (ORM) for the application.
# Each class (Device and Reading) corresponds to a database table.

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, LargeBinary
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
    # New columns
    boardtype: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    binary_file: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    version_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    significance_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
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
    # Specific health metrics
    heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Heart Rate Variability in ms")
    time_in_bed: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Time in bed in hours")
    total_use_time: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Total device use time in hours")

    device: Mapped["Device"] = relationship(back_populates="readings")






