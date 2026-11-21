from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    devices: Mapped[list["Device"]] = relationship(back_populates="owner")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    tariff: Mapped[float] = mapped_column(Float, default=0.18)
    relay_on: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner: Mapped[User] = relationship(back_populates="devices")
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=current_utc_time,
    )
    voltage: Mapped[float] = mapped_column(Float)
    current: Mapped[float] = mapped_column(Float)
    power: Mapped[float] = mapped_column(Float)
    energy_kwh: Mapped[float] = mapped_column(Float)
    frequency: Mapped[float] = mapped_column(Float)
    power_factor: Mapped[float] = mapped_column(Float)
    relay_on: Mapped[bool] = mapped_column(Boolean)

    device: Mapped[Device] = relationship(back_populates="readings")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=current_utc_time,
    )
    message: Mapped[str] = mapped_column(String(255))
    level: Mapped[str] = mapped_column(String(20), default="warning")
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    device: Mapped[Device] = relationship(back_populates="alerts")
