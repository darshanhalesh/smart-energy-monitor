from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..analytics import find_anomaly
from ..db import get_db
from ..models import Alert, Device, Reading, User
from ..schemas import AlertOut, ReadingCreate, ReadingOut
from ..security import get_current_user
from .devices import get_owned_device


router = APIRouter(prefix="/api", tags=["telemetry"])


@router.post("/telemetry/{device_id}", response_model=ReadingOut)
def add_reading(
    device_id: int,
    data: ReadingCreate,
    db: Session = Depends(get_db),
):
    device = db.get(Device, device_id)

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return save_reading(db, device, data)


def save_reading(
    db: Session,
    device: Device,
    data: ReadingCreate,
) -> Reading:
    reading = Reading(
        device_id=device.id,
        voltage=data.voltage,
        current=data.current,
        power=data.power,
        energy_kwh=data.energy_kwh,
        frequency=data.frequency,
        power_factor=data.power_factor,
        relay_on=data.relay_on,
    )

    db.add(reading)
    db.flush()

    add_alert_if_needed(db, device.id, data.power)

    db.commit()
    db.refresh(reading)

    return reading


def add_alert_if_needed(db: Session, device_id: int, power: float) -> None:
    if not find_anomaly(db, device_id, power):
        return

    alert = Alert(
        device_id=device_id,
        message=f"Unusual power reading: {power:.0f} W",
        level="warning",
    )
    db.add(alert)


@router.get("/telemetry/{device_id}/latest", response_model=ReadingOut)
def get_latest_reading(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_device(db, user, device_id)

    query = (
        select(Reading)
        .where(Reading.device_id == device_id)
        .order_by(Reading.timestamp.desc())
    )
    reading = db.scalar(query)

    if reading is None:
        raise HTTPException(status_code=404, detail="No readings yet")

    return reading


@router.get("/telemetry/{device_id}/history", response_model=list[ReadingOut])
def get_history(
    device_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_device(db, user, device_id)

    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = (
        select(Reading)
        .where(
            Reading.device_id == device_id,
            Reading.timestamp >= start_time,
        )
        .order_by(Reading.timestamp)
    )

    return db.scalars(query).all()


@router.get("/alerts/{device_id}", response_model=list[AlertOut])
def get_alerts(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_device(db, user, device_id)

    query = (
        select(Alert)
        .where(Alert.device_id == device_id)
        .order_by(Alert.created_at.desc())
        .limit(20)
    )

    return db.scalars(query).all()


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Alert)
        .join(Device)
        .where(
            Alert.id == alert_id,
            Device.owner_id == user.id,
        )
    )
    alert = db.scalar(query)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = True
    db.commit()

    return {"ok": True}
