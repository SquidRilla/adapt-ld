from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from datetime import timedelta
from app.services.auth_service import authenticate_user, create_access_token
from app.core import security

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, response: Response):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": user["email"]}, expires_delta=access_token_expires)
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
