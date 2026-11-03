"""Text helpers for building semantic-query inputs."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace and strip the result."""
    return _WHITESPACE.sub(" ", text).strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split ``text`` into chunks of at most ``chunk_size`` characters.

    Chunks overlap by ``overlap`` characters so that context is not lost at
    chunk boundaries. Chunking happens on word boundaries when possible.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            last_space = cleaned.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)

    return [chunk for chunk in chunks if chunk]
