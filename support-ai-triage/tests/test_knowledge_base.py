"""
Tests for the knowledge_base module. These don't require an API key,
so they can run in CI on every push.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from knowledge_base import KnowledgeBase, _split_into_chunks  # noqa: E402

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(KB_DIR)


def test_kb_loads_chunks(kb):
    assert len(kb.chunks) > 0


def test_split_into_chunks_basic():
    md = "# Title\n\n## Section One\nSome text here.\n\n## Section Two\nMore text."
    chunks = _split_into_chunks(md, source="test")
    assert len(chunks) == 2
    assert chunks[0].heading == "Section One"
    assert "Some text here" in chunks[0].text
    assert chunks[1].heading == "Section Two"


def test_search_returns_relevant_login_article(kb):
    results = kb.search("can't log in invalid password after reset", top_k=2)
    assert len(results) > 0
    assert any("login" in c.source for c in results)


def test_search_returns_relevant_billing_article(kb):
    results = kb.search("duplicate charge on my credit card refund", top_k=2)
    assert len(results) > 0
    assert any("billing" in c.source for c in results)


def test_search_with_irrelevant_query_still_returns_list(kb):
    results = kb.search("completely unrelated gibberish xyzxyz", top_k=2)
    assert isinstance(results, list)


def test_format_context_empty():
    kb_instance = KnowledgeBase(KB_DIR)
    formatted = kb_instance.format_context([])
    assert "No relevant" in formatted


def test_format_context_includes_source(kb):
    results = kb.search("password reset", top_k=1)
    formatted = kb.format_context(results)
    assert "Source:" in formatted
