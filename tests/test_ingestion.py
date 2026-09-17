import pytest
from fastapi.testclient import TestClient

from pdf_chatbot import api
from pdf_chatbot.core import KnowledgeBase


def test_failure_on_later_page_leaves_index_unchanged():
    kb = KnowledgeBase()
    kb.add_text("Existing Saturn evidence.", "existing.pdf")
    before = kb.search("Saturn")

    def pages():
        yield 1, "New Saturn evidence."
        raise ValueError("damaged page")

    with pytest.raises(ValueError, match="damaged"):
        kb.add_pages(pages(), "broken.pdf")
    assert len(kb) == 1
    assert kb.search("Saturn") == before


def test_extraction_budget_and_empty_document_are_atomic():
    kb = KnowledgeBase()
    for pages in [[(1, " ")], [(1, "x" * 2_000_001)]]:
        with pytest.raises(ValueError):
            kb.add_pages(pages, "bad.pdf")
        assert len(kb) == 0


def test_citations_correspond_only_to_returned_excerpts():
    kb = KnowledgeBase()
    for page in range(1, 5):
        kb.add_text(f"Saturn has rings. Evidence page {page}.", "saturn.pdf", page)
    result = kb.answer("Saturn", limit=4)
    assert len(result["citations"]) == 2
    for citation in result["citations"]:
        assert f"page {citation['page']}" in result["answer"]


def test_api_rejects_blank_questions_and_sanitizes_parser_errors(monkeypatch):
    client = TestClient(api.app)
    assert client.post("/chat", json={"question": "   "}).status_code == 422

    def broken(*args):
        raise ValueError("internal confidential parser detail")

    monkeypatch.setattr(api.knowledge_base, "add_pdf_bytes", broken)
    response = client.post("/documents", files={"file": ("test.pdf", b"bad", "application/pdf")})
    assert response.status_code == 422
    assert "confidential" not in response.text
