"""Unit tests for the knowledge base chunker."""

import pytest
from app.services.kb_chunker import (
    Chunk, load_and_chunk_all, _parse_file, _split_into_chunks,
    _build_prefix, _split_sentences, MAX_CHUNK_CHARS, OVERLAP_CHARS,
)


class TestParseFile:
    def test_extracts_title(self):
        raw = "# Diabetes Type 2\n\nSome body text here."
        meta, body = _parse_file(raw, "diabetes_type_2")
        assert meta["title"] == "Diabetes Type 2"
        assert "Some body text" in body

    def test_extracts_also_called(self):
        raw = "# Test\nAlso known as: T2DM, Type 2\n\nBody."
        meta, body = _parse_file(raw, "test")
        assert meta["also_called"] == "T2DM, Type 2"

    def test_extracts_source_url(self):
        raw = "# Test\n\nBody.\nSource: https://medlineplus.gov/test.html"
        meta, body = _parse_file(raw, "test")
        assert meta["source_url"] == "https://medlineplus.gov/test.html"

    def test_extracts_doc_type_for_drugs(self):
        raw = "# Metformin\nType: Medication / Drug Information\n\nDrug body."
        meta, body = _parse_file(raw, "drug_metformin")
        assert "Medication" in meta["doc_type"]

    def test_body_excludes_metadata_lines(self):
        raw = "# Title\nAlso known as: Alias\nSource: https://example.com\nMeSH: Test (D123)\nCategories: Cat1\n\nActual body content."
        meta, body = _parse_file(raw, "test")
        assert "Actual body content" in body
        assert "Also known as" not in body
        assert "Source:" not in body


class TestBuildPrefix:
    def test_basic_prefix(self):
        meta = {"title": "Diabetes"}
        assert _build_prefix(meta) == "Topic: Diabetes"

    def test_prefix_with_synonyms(self):
        meta = {"title": "A1C", "also_called": "HbA1C, Glycohemoglobin"}
        prefix = _build_prefix(meta)
        assert "A1C" in prefix
        assert "HbA1C" in prefix

    def test_prefix_with_drug_tag(self):
        meta = {"title": "Metformin", "doc_type": "Medication / Drug Information"}
        prefix = _build_prefix(meta)
        assert "[Medication]" in prefix


class TestSplitSentences:
    def test_splits_on_period(self):
        text = "First sentence. Second sentence. Third one."
        sents = _split_sentences(text)
        assert len(sents) >= 2

    def test_keeps_short_text_whole(self):
        text = "Just one sentence."
        sents = _split_sentences(text)
        assert len(sents) == 1


class TestSplitIntoChunks:
    def test_short_text_stays_whole(self):
        meta = {"title": "Short Topic"}
        chunks = _split_into_chunks("A short body.", meta)
        assert len(chunks) == 1
        assert "Short Topic" in chunks[0].text

    def test_long_text_gets_split(self):
        # Create text longer than MAX_CHUNK_CHARS
        sentences = [f"This is sentence number {i} with enough words to make it realistic." for i in range(100)]
        long_text = " ".join(sentences)
        assert len(long_text) > MAX_CHUNK_CHARS

        meta = {"title": "Long Topic"}
        chunks = _split_into_chunks(long_text, meta)
        assert len(chunks) > 1

    def test_all_chunks_have_prefix(self):
        sentences = [f"Sentence {i} is about medical things and health topics." for i in range(100)]
        long_text = " ".join(sentences)
        meta = {"title": "Test Topic"}
        chunks = _split_into_chunks(long_text, meta)
        for chunk in chunks:
            assert "Topic: Test Topic" in chunk.text

    def test_empty_text_returns_nothing(self):
        chunks = _split_into_chunks("", {"title": "Empty"})
        assert len(chunks) == 0

    def test_chunk_metadata_preserved(self):
        meta = {"title": "Test", "source_url": "https://example.com"}
        chunks = _split_into_chunks("Some content here.", meta)
        assert chunks[0].metadata["title"] == "Test"
        assert chunks[0].metadata["source_url"] == "https://example.com"
