from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import SECRET_KEY
from .db import get_db
from .models import User


TOKEN_ALGORITHM = "HS256"
TOKEN_HOURS = 12

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_hasher.verify(password_hash, password)
        return True
    except Exception:
        return False


def create_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)

    token_data = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=TOKEN_ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = read_user_id_from_token(token)
    user = db.get(User, user_id)

    if user is None:
        raise invalid_token_error()

    return user


def read_user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[TOKEN_ALGORITHM],
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise invalid_token_error()


def invalid_token_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
