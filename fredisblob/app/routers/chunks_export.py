
from fastapi import APIRouter, Request, Form
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from app.services.chunks_export_service import generate_chunks_csv, get_all_user_ids
import io

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/chunks_export")
def chunks_export_form(request: Request):
    return templates.TemplateResponse("chunks_export_form.html", {"request": request})

@router.post("/chunks_export")
def export_chunks(request: Request, user_ids: str = Form(""), all_users: bool = Form(False)):
    if all_users:
        user_id_list = get_all_user_ids()
    else:
        user_id_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]

    csv_data = generate_chunks_csv(user_id_list)
    return StreamingResponse(iter([csv_data.getvalue()]), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=chunks_export.csv"
    })
