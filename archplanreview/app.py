from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .extractors import SUPPORTED_EXTENSIONS, extract_plan_pages
from .search import SearchIndex

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = Path.cwd() / "data"


def create_app(data_dir: str | Path = DEFAULT_DATA_DIR) -> FastAPI:
    data_dir = Path(data_dir)
    upload_dir = data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    index = SearchIndex(data_dir / "archplanreview.sqlite")

    app = FastAPI(
        title="ArchPlanReview",
        description="Local-first architectural plan upload, text extraction, and search.",
        version="0.1.0",
    )
    app.state.index = index
    app.state.upload_dir = upload_dir

    static_dir = PACKAGE_DIR / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "app": "ArchPlanReview"}

    @app.get("/api/documents")
    def list_documents() -> dict:
        return {"documents": app.state.index.list_documents()}

    @app.post("/api/documents", status_code=201)
    async def upload_document(file: UploadFile = File(...)) -> dict:
        filename = Path(file.filename or "plan.pdf").name
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Upload PDF, PNG, JPG, or TIFF.")
        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = app.state.upload_dir / stored_name
        with stored_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        try:
            pages = extract_plan_pages(stored_path)
            document_id = app.state.index.add_document(filename, pages, str(stored_path))
        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail=f"Could not process plan: {exc}") from exc
        return {"id": document_id, "filename": filename, "page_count": len(pages)}

    @app.get("/api/search")
    def search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)) -> dict:
        hits = app.state.index.search(q, limit=limit)
        return {"query": q, "results": [hit.__dict__ for hit in hits]}

    @app.get("/api/documents/{document_id}/pages/{page_number}")
    def get_page(document_id: int, page_number: int) -> dict:
        text = app.state.index.get_page_text(document_id, page_number)
        if text is None:
            raise HTTPException(status_code=404, detail="Page not found")
        return {"document_id": document_id, "page_number": page_number, "text": text}

    return app


app = create_app()
