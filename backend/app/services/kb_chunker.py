"""Split processed knowledge base text files into chunks for embedding.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "knowledge_docs" / "processed"

MAX_CHUNK_CHARS = 1500   # ~375 tokens
OVERLAP_CHARS = 200      # ~50 tokens of context preserved across splits


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def load_and_chunk_all(docs_dir: Path = PROCESSED_DIR) -> list[Chunk]:
    """Load every .txt file and return a flat list of chunks."""
    all_chunks = []
    files = sorted(docs_dir.glob("*.txt"))

    if not files:
        logger.warning("No .txt files found in %s", docs_dir)
        return []

    for filepath in files:
        raw = filepath.read_text(encoding="utf-8")
        meta, body = _parse_file(raw, filepath.stem)
        chunks = _split_into_chunks(body, meta)
        all_chunks.extend(chunks)

    logger.info("Created %d chunks from %d files", len(all_chunks), len(files))
    return all_chunks


def _parse_file(raw: str, filename: str) -> tuple[dict, str]:
    """Separate metadata header lines from body text."""
    lines = raw.strip().split("\n")

    meta = {"filename": filename}
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            meta["title"] = stripped[2:].strip()
        elif stripped.startswith("Also known as:"):
            meta["also_called"] = stripped[len("Also known as:"):].strip()
        elif stripped.startswith("Type:"):
            meta["doc_type"] = stripped[len("Type:"):].strip()
        elif stripped.startswith("Source:"):
            meta["source_url"] = stripped[len("Source:"):].strip()
        elif stripped.startswith("MeSH:"):
            meta["mesh"] = stripped[len("MeSH:"):].strip()
        elif stripped.startswith("Categories:"):
            meta["categories"] = stripped[len("Categories:"):].strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    return meta, body


def _split_into_chunks(text: str, metadata: dict) -> list[Chunk]:
    """Split text at sentence boundaries with overlap."""
    if not text:
        return []

    # Short enough — keep as one chunk
    if len(text) <= MAX_CHUNK_CHARS:
        prefix = _build_prefix(metadata)
        return [Chunk(text=f"{prefix}\n\n{text}", metadata=metadata)]

    sentences = _split_sentences(text)
    chunks = []
    current = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent)

        if current and (current_len + sent_len > MAX_CHUNK_CHARS):
            chunk_text = " ".join(current)
            prefix = _build_prefix(metadata)
            chunks.append(Chunk(
                text=f"{prefix}\n\n{chunk_text}",
                metadata={**metadata, "chunk_index": len(chunks)},
            ))

            # Keep trailing sentences as overlap
            overlap = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > OVERLAP_CHARS:
                    break
                overlap.insert(0, s)
                overlap_len += len(s)

            current = overlap
            current_len = overlap_len

        current.append(sent)
        current_len += sent_len

    # Final chunk
    if current:
        chunk_text = " ".join(current)
        prefix = _build_prefix(metadata)
        chunks.append(Chunk(
            text=f"{prefix}\n\n{chunk_text}",
            metadata={**metadata, "chunk_index": len(chunks)},
        ))

    return chunks


def _build_prefix(metadata: dict) -> str:
    """Short header so each chunk identifies its topic."""
    title = metadata.get("title", "")
    also = metadata.get("also_called", "")
    doc_type = metadata.get("doc_type", "")

    prefix = f"Topic: {title}"
    if also:
        prefix += f" (also: {also})"
    if "drug" in doc_type.lower() or "medication" in doc_type.lower():
        prefix += " [Medication]"
    return prefix


def _split_sentences(text: str) -> list[str]:
    """Split on sentence-ending punctuation followed by space + uppercase."""
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [p.strip() for p in parts if p.strip()]


def run():
    """Chunk all processed files and print stats."""
    chunks = load_and_chunk_all()

    if not chunks:
        print("No chunks created. Run kb_sources first.")
        return

    lengths = [len(c.text) for c in chunks]
    drug_chunks = sum(1 for c in chunks if "drug" in c.metadata.get("filename", ""))

    print(f"\nTotal chunks:       {len(chunks)}")
    print(f"  Health topics:    {len(chunks) - drug_chunks}")
    print(f"  Drug/medication:  {drug_chunks}")
    print(f"Avg length:         {sum(lengths) // len(lengths)} chars")
    print(f"Min length:         {min(lengths)} chars")
    print(f"Max length:         {max(lengths)} chars")

    # Show one health topic chunk and one drug chunk
    print(f"\n{'='*60}")
    print("Sample health topic chunk:")
    print(f"{'='*60}")
    for c in chunks:
        if "drug" not in c.metadata.get("filename", ""):
            print(c.text[:400])
            break

    print(f"\n{'='*60}")
    print("Sample drug chunk:")
    print(f"{'='*60}")
    for c in chunks:
        if "drug" in c.metadata.get("filename", ""):
            print(c.text[:400])
            break


if __name__ == "__main__":
    run()