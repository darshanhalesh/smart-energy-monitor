import math
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import DEMO_EMAIL, DEMO_PASSWORD
from .models import Alert, Device, Reading, User
from .security import hash_password


DEMO_TARIFF = 0.18
HOURS_IN_WEEK = 7 * 24


def setup_demo(db: Session) -> None:
    existing_user = db.scalar(select(User).where(User.email == DEMO_EMAIL))

    if existing_user:
        return

    user = create_demo_user(db)
    device = create_demo_device(db, user.id)

    add_demo_history(db, device.id)
    add_demo_alert(db, device.id)

    db.commit()


def create_demo_user(db: Session) -> User:
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    db.flush()
    return user


def create_demo_device(db: Session, owner_id: int) -> Device:
    device = Device(
        name="Living Room",
        tariff=DEMO_TARIFF,
        owner_id=owner_id,
    )
    db.add(device)
    db.flush()
    return device


def add_demo_history(db: Session, device_id: int) -> None:
    current_hour = datetime.now(timezone.utc).replace(
        minute=0,
        second=0,
        microsecond=0,
    )
    total_energy = 0.0

    for index in range(HOURS_IN_WEEK):
        hours_ago = HOURS_IN_WEEK - index
        timestamp = current_hour - timedelta(hours=hours_ago)
        power = make_demo_power(timestamp.hour)
        total_energy += power / 1000

        reading = Reading(
            device_id=device_id,
            timestamp=timestamp,
            voltage=random.uniform(228, 232),
            current=power / 230,
            power=round(power, 2),
            energy_kwh=round(total_energy, 3),
            frequency=random.uniform(59.8, 60.2),
            power_factor=random.uniform(0.90, 0.99),
            relay_on=True,
        )
        db.add(reading)


def make_demo_power(hour: int) -> float:
    base_power = 180 + 120 * math.sin((hour - 7) / 24 * 2 * math.pi)

    if 18 <= hour <= 23:
        base_power += 250

    random_change = random.uniform(-35, 35)
    return max(50, base_power + random_change)


def add_demo_alert(db: Session, device_id: int) -> None:
    alert = Alert(
        device_id=device_id,
        message="Demo alert: unusual power use detected.",
        level="warning",
    )
    db.add(alert)


def add_demo_reading(db: Session, device: Device) -> None:
    previous_energy = get_previous_energy(db, device.id)
    power = get_current_demo_power(device.relay_on)
    new_energy = previous_energy + power / 1000 / 60

    power_factor = 1.0

    if power > 0:
        power_factor = 0.96

    reading = Reading(
        device_id=device.id,
        voltage=random.uniform(228, 232),
        current=power / 230,
        power=round(power, 2),
        energy_kwh=round(new_energy, 3),
        frequency=60.0,
        power_factor=power_factor,
        relay_on=device.relay_on,
    )

    db.add(reading)
    db.commit()


def get_previous_energy(db: Session, device_id: int) -> float:
    query = (
        select(Reading)
        .where(Reading.device_id == device_id)
        .order_by(Reading.timestamp.desc())
    )
    last_reading = db.scalar(query)

    if last_reading is None:
        return 0.0

    return last_reading.energy_kwh


def get_current_demo_power(relay_on: bool) -> float:
    if not relay_on:
        return 0.0

    hour = datetime.now().hour
    base_power = 170

    if 18 <= hour <= 23:
        base_power += 250

    return max(40, base_power + random.uniform(-50, 50))
