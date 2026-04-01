from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.core import security
from jose import JWTError
from fastapi import HTTPException, Request, Depends
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import User, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Remove in-memory store, use DB instead

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + security.get_access_token_expires()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """FastAPI dependency to require authenticated user via HttpOnly cookie 'access_token'."""
    token = request.cookies.get("access_token")
    if not token:
        # If the client expects HTML, redirect to home and open the sign-in modal
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            # preserve original path so we can redirect back after login
            next_path = request.url.path
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": f"/?signin=1&next={next_path}"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            next_path = request.url.path
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": f"/?signin=1&next={next_path}"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = payload.get("sub")
    if email is None:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            next_path = request.url.path
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": f"/?signin=1&next={next_path}"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await get_user(db, email)
    if not user:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            next_path = request.url.path
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": f"/?signin=1&next={next_path}"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)):
    """Return authenticated user if token present and valid, otherwise None.

    This helper can be used in routes that want to render templates even when
    the visitor isn't signed in. It mirrors :func:`get_current_user` but
    suppresses HTTPExceptions and simply returns ``None`` for unauthenticated
    requests.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    return await get_user(db, email)
