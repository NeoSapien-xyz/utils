from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional

from ..services.chunk_loss import analyze_chunk_loss

router = APIRouter(prefix="/chunk_loss")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def chunk_loss_form(request: Request):
    return templates.TemplateResponse("chunk_loss_form.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def run_chunk_loss(request: Request, user_ids: Optional[str] = Form(None), confirm_all: Optional[bool] = Form(False)):
    user_id_list = [uid.strip() for uid in user_ids.split(",")] if user_ids else []

    # Confirmation prompt if no user ID and not confirmed
    if not user_id_list and not confirm_all:
        return templates.TemplateResponse("confirm_all.html", {"request": request})

    result = analyze_chunk_loss(user_id_list)
    return templates.TemplateResponse("chunk_loss_result.html", {"request": request, **result})
