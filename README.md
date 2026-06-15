# ArchPlanReview

ArchPlanReview is a local-first web app for searching architectural plan sets. Upload PDFs or image sheets, index extracted text, then search for rooms, notes, dimensions, sheet references, accessibility terms, fire/life-safety notes, and construction keywords.

## Features

- Upload PDF, PNG, JPG, or TIFF plan files
- Extract text from digital PDFs with PyMuPDF
- Optional image OCR hook using Tesseract + `pytesseract`
- SQLite FTS5 search with prefix matching for partial/OCR-imperfect terms
- Web UI for upload, document listing, search results, snippets, and page text
- FastAPI JSON endpoints for integration with future AI/RAG workflows
- Windows one-click launcher: `run.bat`

## Quick start on Windows

Double-click `run.bat`, then open:

```text
http://127.0.0.1:8000
```

Or run from Git Bash:

```bash
python3 -m venv .venv
. .venv/Scripts/activate
pip install -e '.[dev]'
uvicorn archplanreview.app:app --reload
```

## API

- `GET /api/health` — app health
- `POST /api/documents` — upload a plan file as multipart `file`
- `GET /api/documents` — list indexed documents
- `GET /api/search?q=mechanical%20room` — search indexed plans
- `GET /api/documents/{document_id}/pages/{page_number}` — retrieve extracted text

## Testing

```bash
. .venv/Scripts/activate
pytest -q
```

## OCR notes

Digital PDFs usually work immediately. Scanned/image-only sheets require OCR. To enable image OCR:

1. Install the Tesseract binary for Windows.
2. Install the optional Python dependency:

```bash
pip install -e '.[ocr]'
```

## Roadmap

- Coordinate-aware highlight overlays on top of rendered plan sheets
- Door/window/symbol detection
- AI question-answering with sheet/page citations
- Excel/PDF export of search reports
- Multi-project workspaces and role-based review notes
