from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Reading


def get_recent_power_values(db: Session, device_id: int, limit: int = 20) -> list[float]:
    query = (
        select(Reading.power)
        .where(Reading.device_id == device_id)
        .order_by(Reading.timestamp.desc())
        .limit(limit)
    )
    return list(db.scalars(query).all())


def find_anomaly(db: Session, device_id: int, power: float) -> bool:
    recent_values = get_recent_power_values(db, device_id)

    if len(recent_values) < 5:
        return power > 5000

    average_power = sum(recent_values) / len(recent_values)
    high_limit = max(5000, average_power * 3)

    return power > high_limit


def make_forecast(db: Session, device_id: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)

    query = (
        select(Reading)
        .where(
            Reading.device_id == device_id,
            Reading.timestamp >= one_week_ago,
        )
        .order_by(Reading.timestamp)
    )
    readings = list(db.scalars(query).all())

    if not readings:
        return []

    hourly_values = group_power_by_hour(readings)
    fallback_power = average_power(readings)

    forecast = []
    for hours_ahead in range(24):
        forecast_time = now + timedelta(hours=hours_ahead)
        values_for_hour = hourly_values.get(forecast_time.hour)

        if values_for_hour:
            predicted_power = sum(values_for_hour) / len(values_for_hour)
        else:
            predicted_power = fallback_power

        forecast.append(
            {
                "time": forecast_time.isoformat(),
                "power": round(predicted_power, 2),
            }
        )

    return forecast


def group_power_by_hour(readings: list[Reading]) -> dict[int, list[float]]:
    hourly_values: dict[int, list[float]] = {}

    for reading in readings:
        hour = reading.timestamp.hour

        if hour not in hourly_values:
            hourly_values[hour] = []

        hourly_values[hour].append(reading.power)

    return hourly_values


def average_power(readings: list[Reading]) -> float:
    total_power = sum(reading.power for reading in readings)
    return total_power / len(readings)
