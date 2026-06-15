# Architecture

ArchPlanReview is intentionally small and local-first.

```text
Browser UI -> FastAPI app -> Extractors -> SQLite FTS5
                         -> uploaded files in data/uploads
```

## Modules

- `archplanreview/app.py` — FastAPI routes and static UI hosting
- `archplanreview/extractors.py` — PDF text extraction and optional image OCR
- `archplanreview/search.py` — SQLite schema, document/page persistence, FTS search
- `archplanreview/models.py` — small dataclasses for pages and search hits
- `archplanreview/static/` — no-build browser UI

## Data model

- `documents`: original filename, stored path, upload timestamp
- `pages`: extracted text per document/page
- `page_fts`: SQLite FTS5 virtual table for ranked plan search

## Production upgrade path

For a larger commercial version, add user accounts, project/workspace boundaries, cloud object storage, coordinate-level extraction, async background jobs for large plan sets, and a vector/RAG layer for natural-language answers with sheet citations.
