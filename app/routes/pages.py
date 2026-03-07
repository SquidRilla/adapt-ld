
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Render homepage, optionally passing the authenticated user.

    The ``get_current_user_optional`` helper inspects the cookie and returns a
    user dict or ``None``.  The template can then render the appropriate
    navbar state.
    """
    from app.services.auth_service import get_current_user_optional

    user = None
    try:
        user = get_current_user_optional(request)
    except Exception:
        # swallowing any errors ensures the home page still renders even if
        # token decoding fails for some reason
        user = None

    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@router.get("/test", response_class=HTMLResponse)
def test(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("test.html", {"request": request, "user": user})

@router.get("/adapt-ld/reading")
def reading_page(request: Request):
    return templates.TemplateResponse("reading.html", {"request": request})


@router.get("/attention", response_class=HTMLResponse)
def attention(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("attention.html", {"request": request, "user": user})


@router.get("/math", response_class=HTMLResponse)
def numeracy(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("math.html", {"request": request, "user": user})

@router.get("/result", response_class=HTMLResponse)
def result(request: Request, prediction: str = "No LD Detected"):
    # optionally include user so base.html navbar can adapt
    from app.services.auth_service import get_current_user_optional
    user = None
    try:
        user = get_current_user_optional(request)
    except Exception:
        user = None
    return templates.TemplateResponse(
        "result.html", {"request": request, "prediction": prediction, "user": user}
    )

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@router.get("/logout")
def logout(request: Request):
    """Clears authentication cookie and redirects to home."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response
