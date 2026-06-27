"""
ai_client.py

Thin wrapper around a local LLM (via Ollama) for two tasks:
  1. classify_ticket  - structured classification (category, urgency, sentiment, escalate?)
  2. draft_response   - generates a suggested reply grounded in retrieved KB context

Runs entirely free and offline using Ollama (https://ollama.com) — no API key,
no signup, no cost, no internet connection required after the model is pulled.

Why a local model instead of a paid API:
  - Zero cost, zero usage limits, fully reproducible by anyone who clones this repo
  - No secrets to manage or accidentally leak
  - Demonstrates the system design works independent of which model powers it —
    the same ai_client.py interface could point at Claude, GPT, or any other
    provider by swapping the _call_llm() implementation, without touching
    pipeline.py or knowledge_base.py at all.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"  # free, runs on CPU, ~2GB download via `ollama pull llama3.2`

CLASSIFICATION_SYSTEM_PROMPT = """You are a support ticket triage assistant for a SaaS company.
Given a customer support ticket, classify it and respond with ONLY a JSON object
(no markdown fences, no preamble) with exactly these fields:

{
  "category": one of ["login_account", "billing", "technical_bug", "feature_request", "api_integration", "general_feedback", "other"],
  "urgency": one of ["low", "medium", "high", "critical"],
  "sentiment": one of ["positive", "neutral", "frustrated", "angry"],
  "escalate": true or false,
  "escalation_reason": short string explaining why if escalate is true, else null
}

Rules for escalation (set escalate=true) if ANY apply:
- Customer mentions legal action, lawyers, or regulatory complaints
- Customer is an enterprise/premium tier AND urgency is high or critical
- Customer explicitly threatens to cancel or churn
- Sentiment is "angry"
Otherwise escalate=false.
"""

RESPONSE_SYSTEM_PROMPT = """You are a customer support agent drafting a reply.
Use the provided knowledge base context to ground your answer in actual company policy.
Be warm, concise, and specific. Do not invent policies not present in the context.
If the context doesn't cover the issue, say a specialist will follow up rather than guessing.
Keep the draft under 150 words. Output plain text only, no markdown.
"""


@dataclass
class TicketClassification:
    category: str
    urgency: str
    sentiment: str
    escalate: bool
    escalation_reason: str | None


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server isn't reachable."""


class SupportAIClient:
    """
    Talks to a local Ollama server. Requires:
      1. Ollama installed (https://ollama.com/download) — free, one-time install
      2. The model pulled once:  ollama pull llama3.2
      3. The Ollama app/service running in the background (it usually starts
         automatically after install; otherwise run `ollama serve`)

    No API key. No account. No cost. No data leaves your machine.
    """

    def __init__(self, model: str = MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url
        self._check_connection()

    def _check_connection(self) -> None:
        try:
            self._call_llm(system="ping", prompt="ping", max_tokens=5)
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            raise OllamaConnectionError(
                "Could not reach Ollama at "
                f"{self.base_url}. Make sure Ollama is installed and running:\n"
                "  1. Install: https://ollama.com/download\n"
                "  2. Pull the model once: ollama pull llama3.2\n"
                "  3. Ollama usually runs automatically in the background after install.\n"
                "     If not, start it manually with: ollama serve"
            ) from e

    def _call_llm(self, system: str, prompt: str, max_tokens: int = 300) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3},
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("response", "").strip()

    def classify_ticket(self, subject: str, body: str, customer_tier: str) -> TicketClassification:
        user_message = (
            f"Customer tier: {customer_tier}\n"
            f"Subject: {subject}\n"
            f"Body: {body}"
        )
        raw_text = self._call_llm(system=CLASSIFICATION_SYSTEM_PROMPT, prompt=user_message, max_tokens=300)
        raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        # Small local models sometimes add stray text around the JSON object;
        # extract the first {...} block defensively rather than trusting raw output.
        start, end = raw_text.find("{"), raw_text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Model did not return JSON. Raw output:\n{raw_text}")
        data = json.loads(raw_text[start:end + 1])

        return TicketClassification(
            category=data["category"],
            urgency=data["urgency"],
            sentiment=data["sentiment"],
            escalate=bool(data["escalate"]),
            escalation_reason=data.get("escalation_reason"),
        )

    def draft_response(self, subject: str, body: str, kb_context: str) -> str:
        user_message = (
            f"Customer ticket subject: {subject}\n"
            f"Customer ticket body: {body}\n\n"
            f"Relevant knowledge base context:\n{kb_context}\n\n"
            "Draft a reply to the customer."
        )
        return self._call_llm(system=RESPONSE_SYSTEM_PROMPT, prompt=user_message, max_tokens=300)
