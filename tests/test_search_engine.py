from pathlib import Path

import fitz

from archplanreview.search import SearchIndex
from archplanreview.extractors import extract_pdf_pages


def make_plan_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "SHEET A-101 FIRST FLOOR PLAN", fontsize=14)
    page.insert_text((72, 120), "Mechanical Room 101 includes sprinkler riser and electrical panel.", fontsize=10)
    page.insert_text((72, 150), "Door D-12: 36 inch clear width. ADA accessible route.", fontsize=10)
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((72, 72), "SHEET A-201 SECOND FLOOR PLAN", fontsize=14)
    page2.insert_text((72, 120), "Conference Room 205 has Type X gypsum at rated wall.", fontsize=10)
    doc.save(path)
    doc.close()


def test_extract_pdf_pages_preserves_sheet_text_and_page_numbers(tmp_path):
    pdf = tmp_path / "plans.pdf"
    make_plan_pdf(pdf)

    pages = extract_pdf_pages(pdf)

    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Mechanical Room 101" in pages[0].text
    assert pages[1].page_number == 2
    assert "Type X gypsum" in pages[1].text


def test_search_index_returns_relevant_plan_hits_with_snippets(tmp_path):
    pdf = tmp_path / "plans.pdf"
    make_plan_pdf(pdf)
    pages = extract_pdf_pages(pdf)
    index = SearchIndex(tmp_path / "plans.sqlite")
    document_id = index.add_document("plans.pdf", pages)

    hits = index.search("sprinkler electrical panel")

    assert hits
    assert hits[0].document_id == document_id
    assert hits[0].page_number == 1
    assert "sprinkler" in hits[0].snippet.lower()
    assert "electrical" in hits[0].snippet.lower()


def test_search_index_supports_fuzzy_like_partial_architecture_terms(tmp_path):
    index = SearchIndex(tmp_path / "plans.sqlite")
    index.add_document("notes.pdf", [type("Page", (), {"page_number": 7, "text": "Accessible egress path near stair B."})()])

    hits = index.search("egres")

    assert len(hits) == 1
    assert hits[0].page_number == 7
