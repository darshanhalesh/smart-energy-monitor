from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Device, User
from ..mqtt import publish_command
from ..schemas import DeviceCreate, DeviceOut, RelayRequest
from ..security import get_current_user


router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_owned_device(db: Session, user: User, device_id: int) -> Device:
    query = select(Device).where(
        Device.id == device_id,
        Device.owner_id == user.id,
    )
    device = db.scalar(query)

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.get("", response_model=list[DeviceOut])
def list_devices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Device).where(Device.owner_id == user.id)
    return db.scalars(query).all()


@router.post("", response_model=DeviceOut)
def create_device(
    data: DeviceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = Device(
        name=data.name,
        tariff=data.tariff,
        owner_id=user.id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.post("/{device_id}/control", response_model=DeviceOut)
def control_device(
    device_id: int,
    data: RelayRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = get_owned_device(db, user, device_id)
    device.relay_on = data.relay_on

    db.commit()
    db.refresh(device)

    publish_command(device.id, device.relay_on)
    return device
