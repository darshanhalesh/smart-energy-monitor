import os
from pathlib import Path

TEST_DATABASE = Path("test.db")

if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MQTT_ENABLED"] = "false"
os.environ["DEMO_MODE"] = "false"

from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


Base.metadata.create_all(bind=engine)
client = TestClient(app)


def register_user(email: str = "student@example.com") -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )
    assert response.status_code == 200


def login_user(email: str = "student@example.com") -> str:
    response = client.post(
        "/api/auth/token",
        data={
            "username": email,
            "password": "password123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    register_user()
    token = login_user()

    assert token


def test_devices_require_login():
    response = client.get("/api/devices")

    assert response.status_code == 401


def test_create_device_and_read_dashboard():
    email = "dashboard@example.com"
    register_user(email)
    token = login_user(email)
    headers = auth_headers(token)

    device_response = client.post(
        "/api/devices",
        headers=headers,
        json={"name": "Desk", "tariff": 0.18},
    )
    assert device_response.status_code == 200
    device_id = device_response.json()["id"]

    reading_response = client.post(
        f"/api/telemetry/{device_id}",
        json={
            "voltage": 230,
            "current": 1.0,
            "power": 230,
            "energy_kwh": 1.5,
            "frequency": 60,
            "power_factor": 0.95,
            "relay_on": True,
        },
    )
    assert reading_response.status_code == 200

    dashboard_response = client.get(
        f"/api/dashboard/{device_id}",
        headers=headers,
    )
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["latest"]["power"] == 230


def teardown_module():
    engine.dispose()

    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()
