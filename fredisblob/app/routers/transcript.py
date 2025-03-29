from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..services.transcript import format_transcript_from_json

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/transcript")

@router.get("/", response_class=HTMLResponse)
async def transcript_viewer(request: Request):
    return templates.TemplateResponse("transcript.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def process_transcript(request: Request, file: UploadFile):
    try:
        contents = await file.read()
        import json
        raw_data = json.loads(contents)
        formatted = format_transcript_from_json(raw_data)

        return templates.TemplateResponse("transcript.html", {
            "request": request,
            "transcript": formatted
        })

    except Exception as e:
        return templates.TemplateResponse("transcript.html", {
            "request": request,
            "transcript": None,
            "error": str(e)
        })

