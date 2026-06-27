"""
knowledge_base.py

A lightweight retrieval module over the markdown knowledge base.
Uses TF-IDF + cosine similarity rather than a vector DB, so the
project runs with zero external services and no API key required
for the retrieval step itself (only the LLM calls need a key).

This keeps the project runnable end-to-end by anyone who clones it,
while still demonstrating real retrieval-augmented generation (RAG)
mechanics rather than hand-waving it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class KBChunk:
    source: str
    heading: str
    text: str


def _split_into_chunks(markdown_text: str, source: str) -> list[KBChunk]:
    """Split a markdown file into chunks by ## headings."""
    sections = re.split(r"\n(?=## )", markdown_text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.splitlines()
        heading = lines[0].lstrip("#").strip() if lines[0].startswith("#") else source
        body = "\n".join(lines[1:]).strip() if lines[0].startswith("#") else section
        if body:
            chunks.append(KBChunk(source=source, heading=heading, text=body))
    return chunks


class KnowledgeBase:
    """Loads markdown KB articles and supports similarity-based retrieval."""

    def __init__(self, kb_dir: str | Path):
        self.kb_dir = Path(kb_dir)
        self.chunks: list[KBChunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._load()

    def _load(self) -> None:
        for md_file in sorted(self.kb_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            self.chunks.extend(_split_into_chunks(text, md_file.stem))

        if not self.chunks:
            raise ValueError(f"No knowledge base articles found in {self.kb_dir}")

        corpus = [f"{c.heading}\n{c.text}" for c in self.chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 2) -> list[KBChunk]:
        """Return the top_k most relevant KB chunks for a query string."""
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        ranked_indices = scores.argsort()[::-1][:top_k]
        return [self.chunks[i] for i in ranked_indices if scores[i] > 0]

    def format_context(self, chunks: list[KBChunk]) -> str:
        if not chunks:
            return "No relevant knowledge base articles found."
        parts = []
        for c in chunks:
            parts.append(f"[Source: {c.source} \u2013 {c.heading}]\n{c.text}")
        return "\n\n".join(parts)
