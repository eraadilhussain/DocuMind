import httpx
import pdfplumber
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
from typing import Optional


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts all text from a PDF file using pdfplumber."""
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
    return "\n\n".join(texts)


def extract_text_from_docx(file_path: str) -> str:
    """Extracts all paragraph text from a DOCX file."""
    doc = DocxDocument(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_url(url: str, timeout: int = 15) -> str:
    """
    Fetches a URL and extracts readable text using BeautifulSoup.
    Strips scripts, styles, and navigation boilerplate.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; DocuMind/1.0; +https://github.com/docuMind)"
        )
    }
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    # Prefer <article> / <main> content; fall back to <body>
    main_content = soup.find("article") or soup.find("main") or soup.find("body")
    if main_content is None:
        return soup.get_text(separator="\n", strip=True)

    return main_content.get_text(separator="\n", strip=True)
