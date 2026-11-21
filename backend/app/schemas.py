from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    tariff: float = Field(default=0.18, ge=0)


class DeviceOut(BaseModel):
    id: int
    name: str
    tariff: float
    relay_on: bool

    model_config = {"from_attributes": True}


class RelayRequest(BaseModel):
    relay_on: bool


class ReadingCreate(BaseModel):
    voltage: float
    current: float
    power: float
    energy_kwh: float
    frequency: float
    power_factor: float
    relay_on: bool


class ReadingOut(ReadingCreate):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    created_at: datetime
    message: str
    level: str
    acknowledged: bool

    model_config = {"from_attributes": True}
