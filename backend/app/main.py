import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import DEMO_MODE
from .db import Base, SessionLocal, engine
from .demo import setup_demo
from .demo_loop import run_demo_loop
from .models import Device
from .mqtt import start_mqtt
from .routers import analytics, auth, dashboard, devices, telemetry
from .schemas import ReadingCreate


def handle_mqtt_telemetry(device_id_text: str, data: dict) -> None:
    db = SessionLocal()

    try:
        device_id = int(device_id_text)
        device = db.get(Device, device_id)

        if device is None:
            return

        reading_data = ReadingCreate.model_validate(data)
        telemetry.save_reading(db, device, reading_data)
    except Exception as error:
        print("Telemetry error:", error)
    finally:
        db.close()


def prepare_database() -> None:
    Base.metadata.create_all(bind=engine)

    if not DEMO_MODE:
        return

    db = SessionLocal()

    try:
        setup_demo(db)
    finally:
        db.close()


def start_demo_thread() -> None:
    if not DEMO_MODE:
        return

    thread = threading.Thread(target=run_demo_loop, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    prepare_database()
    start_demo_thread()
    start_mqtt(handle_mqtt_telemetry)
    yield


app = FastAPI(
    title="Smart Energy Monitor",
    version="1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
