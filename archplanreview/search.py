from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import ExtractedPage, SearchHit

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']*")


class SearchIndex:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    stored_path TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    UNIQUE(document_id, page_number)
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS page_fts USING fts5(
                    text,
                    filename UNINDEXED,
                    document_id UNINDEXED,
                    page_number UNINDEXED,
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )

    def add_document(self, filename: str, pages: Iterable[ExtractedPage], stored_path: str | None = None) -> int:
        page_list = list(pages)
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO documents(filename, stored_path) VALUES (?, ?)", (filename, stored_path))
            document_id = int(cur.lastrowid)
            for page in page_list:
                conn.execute(
                    "INSERT INTO pages(document_id, page_number, text) VALUES (?, ?, ?)",
                    (document_id, int(page.page_number), page.text),
                )
                conn.execute(
                    "INSERT INTO page_fts(text, filename, document_id, page_number) VALUES (?, ?, ?, ?)",
                    (page.text, filename, document_id, int(page.page_number)),
                )
        return document_id

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT d.id, d.filename, d.created_at, COUNT(p.id) AS page_count
                FROM documents d LEFT JOIN pages p ON p.document_id = d.id
                GROUP BY d.id
                ORDER BY d.created_at DESC, d.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_page_text(self, document_id: int, page_number: int) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT text FROM pages WHERE document_id = ? AND page_number = ?",
                (document_id, page_number),
            ).fetchone()
        return None if row is None else str(row["text"])

    def page_count(self, document_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM pages WHERE document_id = ?", (document_id,)).fetchone()
        return int(row["n"] if row else 0)

    def search(self, query: str, limit: int = 20) -> list[SearchHit]:
        query = query.strip()
        if not query:
            return []
        fts_query = self._build_fts_query(query)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT document_id, filename, page_number,
                       snippet(page_fts, 0, '[', ']', ' … ', 18) AS snippet,
                       bm25(page_fts) AS score
                FROM page_fts
                WHERE page_fts MATCH ?
                ORDER BY bm25(page_fts)
                LIMIT ?
                """,
                (fts_query, int(limit)),
            ).fetchall()
        return [
            SearchHit(
                document_id=int(row["document_id"]),
                filename=str(row["filename"]),
                page_number=int(row["page_number"]),
                snippet=_clean_snippet(str(row["snippet"])),
                score=float(row["score"]),
            )
            for row in rows
        ]

    def _build_fts_query(self, query: str) -> str:
        tokens = TOKEN_RE.findall(query)
        if not tokens:
            return '""'
        return " OR ".join(f'"{token}"*' for token in tokens[:12])


def _clean_snippet(snippet: str) -> str:
    return " ".join(snippet.replace("\n", " ").split())
