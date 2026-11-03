"""Smoke tests for the package skeleton."""

from aidm_semantic_query import main
from aidm_semantic_query.utils.text import chunk_text, normalize_whitespace


def test_main_is_callable() -> None:
    assert callable(main)


def test_normalize_whitespace() -> None:
    assert normalize_whitespace("  hello \n\t world  ") == "hello world"


def test_chunk_text_returns_overlapping_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_text(text, chunk_size=100, overlap=10)

    assert chunks
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert chunks[0].startswith("word0")


def test_chunk_text_handles_empty_input() -> None:
    assert chunk_text("   ") == []


def test_chunk_text_rejects_invalid_overlap() -> None:
    try:
        chunk_text("some text", chunk_size=10, overlap=10)
    except ValueError:
        pass
    else:  # pragma: no cover - only hit on regression
        raise AssertionError("expected ValueError for overlap >= chunk_size")
