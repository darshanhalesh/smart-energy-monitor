import time

from sqlalchemy import select

from .db import SessionLocal
from .demo import add_demo_reading
from .models import Device


DEMO_UPDATE_SECONDS = 5


def run_demo_loop() -> None:
    while True:
        add_readings_for_all_devices()
        time.sleep(DEMO_UPDATE_SECONDS)


def add_readings_for_all_devices() -> None:
    db = SessionLocal()

    try:
        devices = db.scalars(select(Device)).all()

        for device in devices:
            add_demo_reading(db, device)
    except Exception as error:
        print("Demo loop error:", error)
    finally:
        db.close()
