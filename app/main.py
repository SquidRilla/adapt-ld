
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import pages, assessment, speech, analytics
from app.api import math, attention, auth, reports

app = FastAPI(title="ADAPT-LD")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(assessment.router)
app.include_router(speech.router)
app.include_router(analytics.router)
app.include_router(math.router)
app.include_router(attention.router)
app.include_router(auth.router)
app.include_router(reports.router) 
# Mount auth-protected static for reports if needed (no change required)

