
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import get_current_user, get_current_user_optional
from app.core.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@router.get("/test", response_class=HTMLResponse)
async def test(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("test.html", {"request": request, "user": user})

@router.get("/reading", response_class=HTMLResponse)
async def reading_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reading.html", {"request": request, "user": user})

@router.get("/grammar", response_class=HTMLResponse)
async def grammar(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("grammar.html", {"request": request, "user": user})

@router.get("/attention", response_class=HTMLResponse)
async def attention(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("attention.html", {"request": request, "user": user})

@router.get("/math", response_class=HTMLResponse)
async def numeracy(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("math.html", {"request": request, "user": user})

@router.get("/result", response_class=HTMLResponse)
async def result(request: Request, prediction: str = "No LD Detected", db: AsyncSession = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse("result.html", {"request": request, "prediction": prediction, "user": user})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports.html", {"request": request, "user": user})

@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response
