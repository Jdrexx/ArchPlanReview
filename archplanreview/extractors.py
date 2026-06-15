from __future__ import annotations

from pathlib import Path

import fitz

from .models import ExtractedPage

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def extract_pdf_pages(path: str | Path) -> list[ExtractedPage]:
    """Extract text from every PDF page using PyMuPDF."""
    path = Path(path)
    pages: list[ExtractedPage] = []
    with fitz.open(path) as doc:
        for idx, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append(ExtractedPage(page_number=idx, text=normalize_plan_text(text)))
    return pages


def extract_image_text(path: str | Path) -> str:
    """OCR a single image if pytesseract/Tesseract are available."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image
    except Exception:
        return "[OCR not installed. Install with: pip install -e .[ocr] and install the Tesseract binary.]"
    try:
        return normalize_plan_text(pytesseract.image_to_string(Image.open(path)))
    except Exception as exc:
        return f"[OCR failed: {exc}]"


def extract_plan_pages(path: str | Path) -> list[ExtractedPage]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf_pages(path)
    if ext in SUPPORTED_EXTENSIONS:
        return [ExtractedPage(page_number=1, text=extract_image_text(path))]
    raise ValueError(f"Unsupported plan format: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")


def normalize_plan_text(text: str) -> str:
    lines = (line.strip() for line in text.replace("\x00", " ").splitlines())
    return "\n".join(line for line in lines if line)
