from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Reading, User
from ..security import get_current_user
from .devices import get_owned_device


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{device_id}")
def get_dashboard(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = get_owned_device(db, user, device_id)
    latest_reading = get_latest_reading(db, device_id)
    energy_kwh = get_total_energy(db, device_id)

    return {
        "device": {
            "id": device.id,
            "name": device.name,
            "tariff": device.tariff,
            "relay_on": device.relay_on,
        },
        "latest": latest_reading,
        "energy_kwh": round(energy_kwh, 2),
        "estimated_cost": round(energy_kwh * device.tariff, 2),
        "updated_at": datetime.now(timezone.utc),
    }


def get_latest_reading(db: Session, device_id: int) -> Reading:
    query = (
        select(Reading)
        .where(Reading.device_id == device_id)
        .order_by(Reading.timestamp.desc())
    )
    reading = db.scalar(query)

    if reading is None:
        raise HTTPException(status_code=404, detail="No readings yet")

    return reading


def get_total_energy(db: Session, device_id: int) -> float:
    query = (
        select(Reading)
        .where(Reading.device_id == device_id)
        .order_by(Reading.timestamp.desc())
        .limit(500)
    )
    readings = db.scalars(query).all()

    if not readings:
        return 0.0

    return max(reading.energy_kwh for reading in readings)
