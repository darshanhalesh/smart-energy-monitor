from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..analytics import make_forecast
from ..db import get_db
from ..models import User
from ..security import get_current_user
from .devices import get_owned_device


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{device_id}/forecast")
def get_forecast(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_device(db, user, device_id)

    forecast = make_forecast(db, device_id)
    return {"forecast": forecast}
