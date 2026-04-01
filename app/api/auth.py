from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import authenticate_user, get_user, verify_password, create_access_token, pwd_context
from app.core import security
from app.core.database import User, get_db

router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    from sqlalchemy.future import select
    result = await db.execute(select(User).where(User.email == req.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = pwd_context.hash(req.password)
    new_user = User(name=req.name, email=req.email, password_hash=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Auto-login
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": new_user.email}, expires_delta=access_token_expires)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": user.email}, expires_delta=access_token_expires)
    # Set HttpOnly cookie for the access token
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
    )
    return {"access_token": token, "token_type": "bearer"}
