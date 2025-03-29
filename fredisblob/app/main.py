from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .routers import home, transcript, chunk

app = FastAPI(title="FredisBlob")

# Static + Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(home.router)
app.include_router(transcript.router)
app.include_router(chunk.router)

