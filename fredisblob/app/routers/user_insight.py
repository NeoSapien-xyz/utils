from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from app.services.user_insight_service import fetch_user_memories, get_memory_json
from fastapi.templating import Jinja2Templates
import io
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/user_insight", response_class=HTMLResponse)
async def user_insight_ui(request: Request):
    return templates.TemplateResponse("user_insight.html", {"request": request})

@router.get("/user_insight/data")
async def user_insight_data(
    user_id: str,
    memory_id: str = None,
    started_at: int = None,
    finished_at: int = None,
    page: int = 1,
    page_size: int = 10
):
    results = await fetch_user_memories(
        user_id=user_id,
        memory_id=memory_id,
        started_at=started_at,
        finished_at=finished_at,
        page=page,
        page_size=page_size
    )
    return JSONResponse(content=results)

@router.get("/user_insight/download_memory/{user_id}/{memory_id}")
async def download_memory_json(user_id: str, memory_id: str):
    memory = await get_memory_json(user_id, memory_id)
    buffer = io.BytesIO()
    buffer.write(json.dumps(memory, indent=2).encode("utf-8"))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/json", headers={
        "Content-Disposition": f"attachment; filename={memory_id}.json"
    })

