from pathlib import Path

from fastapi.testclient import TestClient
import fitz

from archplanreview.app import create_app


def make_plan_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "SHEET M-101 MECHANICAL PLAN", fontsize=14)
    page.insert_text((72, 120), "AHU-1 is located in Mechanical Room 101 above ceiling.", fontsize=10)
    doc.save(path)
    doc.close()


def test_upload_search_and_document_page_text_flow(tmp_path):
    app = create_app(data_dir=tmp_path / "data")
    client = TestClient(app)
    pdf = tmp_path / "mechanical.pdf"
    make_plan_pdf(pdf)

    with pdf.open("rb") as handle:
        response = client.post("/api/documents", files={"file": ("mechanical.pdf", handle, "application/pdf")})
    assert response.status_code == 201
    doc_payload = response.json()
    assert doc_payload["filename"] == "mechanical.pdf"
    assert doc_payload["page_count"] == 1

    search = client.get("/api/search", params={"q": "AHU mechanical room"})
    assert search.status_code == 200
    results = search.json()["results"]
    assert len(results) == 1
    assert results[0]["page_number"] == 1
    assert "AHU" in results[0]["snippet"]

    page = client.get(f"/api/documents/{doc_payload['id']}/pages/1")
    assert page.status_code == 200
    assert "Mechanical Room 101" in page.json()["text"]


def test_health_endpoint_reports_ready(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path / "data"))
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
