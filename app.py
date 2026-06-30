import os
import io
import json
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from utils import (
    extract_pdf_text,
    fetch_job_description,
    search_company,
    generate_interview_brief,
)

app = FastAPI()

# Mount static assets (css, js)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_brief(
    request: Request,
    resume: UploadFile = File(...),
    job_url: str = Form(...),
):
    # Validate PDF
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF file")
    # Read PDF bytes
    pdf_bytes = await resume.read()
    # Extract text
    resume_text = extract_pdf_text(pdf_bytes)
    # Fetch job description
    job_desc = await fetch_job_description(job_url)
    # Company research (using domain extraction)
    company_info = await search_company(job_url)
    # Generate brief via Gemini
    brief = await generate_interview_brief(resume_text, job_desc, company_info)
    return JSONResponse(content=brief)

# Optional endpoint to download as PDF (client‑side print is fine, but we provide server‑side).
@app.get("/download")
async def download_brief(content: str):
    html = f"<html><body>{content}</body></html>"
    # Convert HTML to PDF using weasyprint (optional, may require extra deps)
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=interview_brief.pdf"})
    except Exception:
        raise HTTPException(status_code=500, detail="PDF generation failed")
