"""
Tests for ai_client.py. Mocks the HTTP call to the local Ollama server,
so these run in CI without needing Ollama actually installed or running.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_client import OllamaConnectionError, SupportAIClient, TicketClassification  # noqa: E402


def _mock_urlopen(response_text: str):
    """Build a mock for urllib.request.urlopen that returns an Ollama-shaped response."""
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = json.dumps(
        {"response": response_text}
    ).encode("utf-8")
    return mock_cm


@pytest.fixture
def client():
    with patch("ai_client.urllib.request.urlopen", return_value=_mock_urlopen("pong")):
        return SupportAIClient()


def test_raises_clear_error_when_ollama_not_running():
    with patch("ai_client.urllib.request.urlopen", side_effect=ConnectionRefusedError()):
        with pytest.raises(OllamaConnectionError, match="ollama.com/download"):
            SupportAIClient()


def test_classify_ticket_parses_json_response(client):
    fake_json = json.dumps({
        "category": "billing",
        "urgency": "high",
        "sentiment": "frustrated",
        "escalate": True,
        "escalation_reason": "duplicate charge, premium tier",
    })
    with patch("ai_client.urllib.request.urlopen", return_value=_mock_urlopen(fake_json)):
        result = client.classify_ticket("Double charged", "I was charged twice", "premium")

    assert isinstance(result, TicketClassification)
    assert result.category == "billing"
    assert result.urgency == "high"
    assert result.escalate is True
    assert result.escalation_reason == "duplicate charge, premium tier"


def test_classify_ticket_strips_markdown_fences(client):
    fake_json = "```json\n" + json.dumps({
        "category": "general_feedback",
        "urgency": "low",
        "sentiment": "positive",
        "escalate": False,
        "escalation_reason": None,
    }) + "\n```"
    with patch("ai_client.urllib.request.urlopen", return_value=_mock_urlopen(fake_json)):
        result = client.classify_ticket("Thanks!", "Great support", "standard")

    assert result.category == "general_feedback"
    assert result.escalate is False
    assert result.escalation_reason is None


def test_classify_ticket_handles_stray_text_around_json(client):
    """Small local models sometimes wrap JSON in extra commentary."""
    fake_json = "Sure, here's the classification:\n" + json.dumps({
        "category": "technical_bug",
        "urgency": "medium",
        "sentiment": "neutral",
        "escalate": False,
        "escalation_reason": None,
    }) + "\nLet me know if you need anything else!"
    with patch("ai_client.urllib.request.urlopen", return_value=_mock_urlopen(fake_json)):
        result = client.classify_ticket("App bug", "Something broke", "standard")

    assert result.category == "technical_bug"


def test_classify_ticket_raises_on_non_json_response(client):
    with patch("ai_client.urllib.request.urlopen", return_value=_mock_urlopen("I cannot help with that.")):
        with pytest.raises(ValueError, match="did not return JSON"):
            client.classify_ticket("Subject", "Body", "standard")


def test_draft_response_returns_text(client):
    with patch(
        "ai_client.urllib.request.urlopen",
        return_value=_mock_urlopen("Thanks for reaching out, we'll fix this right away."),
    ):
        draft = client.draft_response("Login issue", "Can't log in", "Some KB context")
    assert "Thanks for reaching out" in draft
