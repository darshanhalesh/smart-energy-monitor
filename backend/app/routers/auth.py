from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import RegisterRequest, TokenOut, UserOut
from ..security import create_token, get_current_user, hash_password, verify_password


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = data.email.lower().strip()
    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/token", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form.username.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    password_is_correct = verify_password(form.password, user.password_hash)

    if not password_is_correct:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_token(user.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user
