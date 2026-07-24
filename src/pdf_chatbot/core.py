from __future__ import annotations

import io
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Split text at natural boundaries while retaining a small context overlap."""
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        if end < len(clean):
            boundary = max(clean.rfind(". ", start, end), clean.rfind(" ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append(clean[start:end].strip())
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    page: int


@dataclass(frozen=True)
class SearchResult:
    text: str
    source: str
    page: int
    score: float


class KnowledgeBase:
    """A compact BM25 index designed for private, local PDF retrieval."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._tokens: list[list[str]] = []
        self._document_frequency: Counter[str] = Counter()

    def __len__(self) -> int:
        return len(self._chunks)

    def add_text(self, text: str, source: str = "document", page: int = 1) -> int:
        pieces = chunk_text(text)
        for piece in pieces:
            tokens = tokenize(piece)
            self._chunks.append(Chunk(piece, source, page))
            self._tokens.append(tokens)
            self._document_frequency.update(set(tokens))
        return len(pieces)

    def add_pages(self, pages: Iterable[tuple[int, str]], source: str) -> int:
        return sum(self.add_text(text, source, page) for page, text in pages if text.strip())

    def add_pdf_bytes(self, data: bytes, source: str = "document.pdf") -> int:
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("Install pypdf to ingest PDF files") from exc
        reader = PdfReader(io.BytesIO(data))
        pages = ((index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages))
        return self.add_pages(pages, source)

    def search(self, query: str, limit: int = 4) -> list[SearchResult]:
        if limit < 1:
            raise ValueError("limit must be positive")
        terms = tokenize(query)
        if not terms or not self._chunks:
            return []
        total = len(self._chunks)
        avg_length = sum(map(len, self._tokens)) / total
        scored: list[tuple[float, int]] = []
        for index, tokens in enumerate(self._tokens):
            frequencies = Counter(tokens)
            score = 0.0
            for term in terms:
                frequency = frequencies[term]
                if not frequency:
                    continue
                document_frequency = self._document_frequency[term]
                inverse_frequency = math.log(1 + (total - document_frequency + 0.5) / (document_frequency + 0.5))
                length_adjustment = frequency + 1.2 * (0.25 + 0.75 * len(tokens) / max(avg_length, 1))
                score += inverse_frequency * frequency * 2.2 / length_adjustment
            if score:
                scored.append((score, index))
        scored.sort(reverse=True)
        return [
            SearchResult(
                text=self._chunks[index].text,
                source=self._chunks[index].source,
                page=self._chunks[index].page,
                score=round(score, 4),
            )
            for score, index in scored[:limit]
        ]

    def answer(self, question: str, limit: int = 4) -> dict[str, object]:
        """Return an extractive answer that never claims knowledge outside the PDF."""
        results = self.search(question, limit)
        if not results:
            return {
                "answer": "I could not find relevant information in the uploaded PDFs.",
                "citations": [],
            }
        answer = "\n\n".join(result.text for result in results[:2])
        citations = [
            {"source": result.source, "page": result.page, "score": result.score}
            for result in results
        ]
        return {"answer": answer, "citations": citations}

