from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from datetime import datetime
from collections import defaultdict
from app.services.chunk_loss import analyze_chunk_loss
from app.services.trend_utils import extract_trend_data_by_user, build_daily_user_memory_map

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/chunk_trends")
def chunk_trend_form(request: Request):
    return templates.TemplateResponse("chunk_trends_form.html", {"request": request})

@router.post("/chunk_trends")
def chunk_trend_graph(request: Request, user_ids: str = Form(...), debug: bool = Form(False)):
    user_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]

    if not user_list:
        raise HTTPException(status_code=400, detail="User ID list cannot be empty.")

    result = analyze_chunk_loss(user_list)
    per_user_trends = extract_trend_data_by_user(result, include_tooltip=True)
    daily_breakdown = build_daily_user_memory_map(result)

    return templates.TemplateResponse("chunk_trends.html", {
        "request": request,
        "per_user_trends": per_user_trends,
        "daily_user_memory_map": daily_breakdown,
        "user_ids": user_ids,
        "debug": debug
    })