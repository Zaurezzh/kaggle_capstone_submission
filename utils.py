import os
import io
import re
import json
import asyncio
from typing import Dict, Any

import httpx
from pypdf import PdfReader
from ddgs import DDGS  # DuckDuckGo search library
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure Gemini API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY is missing. Please set it in the .env file.")
genai.configure(api_key=api_key)



def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF file given as bytes.
    Returns the concatenated text of all pages.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)

async def fetch_job_description(url: str) -> str:
    """Fetch the HTML of the job posting URL and return the visible job description text.
    Uses httpx with a timeout and a simple HTML->text extraction.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        # Very simple extraction: strip HTML tags (could be improved with BeautifulSoup)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        # Try common selectors for job description
        for selector in [".description", "#job-description", "article", "section"]:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(separator="\n", strip=True)
        # Fallback to full body text
        return soup.get_text(separator="\n", strip=True)

async def search_company(job_url: str) -> str:
    """Derive a company name/domain from the job URL and perform a DuckDuckGo search.
    Returns a short summary of recent news, values, and likely competencies.
    """
    # Extract domain
    from urllib.parse import urlparse
    parsed = urlparse(job_url)
    domain = parsed.netloc
    # Basic query
    query = f"{domain} company overview recent news values interview competencies"
    # Use DDGS to perform a text search and collect top snippets
    snippets = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=5):
            # Each result is a dict with keys like 'title', 'href', 'body'
            body = result.get('body') or result.get('snippet')
            if body:
                snippets.append(body)
    return "\n\n".join(snippets)

async def generate_interview_brief(resume_text: str, job_desc: str, company_info: str) -> Dict[str, Any]:
    """Call Gemini with a crafted prompt and return the structured brief.
    The function builds a single message with instructions and expects a JSON response.
    """
    # Build prompt
    system_prompt = (
        "You are an interview preparation assistant. Using the provided resume text, job description, "
        "and company information, generate a concise interview brief. Return the result as a JSON object with "
        "the following keys: snapshot, company_intel, questions (list), answers (list of STAR answers), "
        "smart_questions (list), talking_points (list)."
    )
    user_prompt = (
        f"Resume:\n{resume_text}\n\nJob Description:\n{job_desc}\n\nCompany Info:\n{company_info}\n"
    )
    model = genai.GenerativeModel("gemini-flash-latest")
    response = model.generate_content([system_prompt, user_prompt], generation_config={"response_mime_type": "application/json"})
    # The response may be a string; try to parse JSON safely
    try:
        content = response.text
        data = json.loads(content)
    except Exception as e:
        # Fallback: return raw text under a single key
        data = {"error": str(e), "raw": response.text}
    return data
