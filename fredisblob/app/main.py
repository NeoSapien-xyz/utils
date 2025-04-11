from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .routers import home, transcript, chunk, chunk_trends, chunks_export, user_insight

app = FastAPI(title="FredisBlob")

# Static + Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(home.router)
app.include_router(transcript.router)
app.include_router(chunk.router)
app.include_router(chunk_trends.router)
app.include_router(chunks_export.router)
app.include_router(user_insight.router)
