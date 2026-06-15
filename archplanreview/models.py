from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class SearchHit:
    document_id: int
    filename: str
    page_number: int
    snippet: str
    score: float
