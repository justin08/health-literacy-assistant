"""Parse MedlinePlus health topics XML and drug JSON into clean text files.

Reads two sources:
  1. Health Topics XML (conditions, labs, diseases) from raw/mplus_topics.xml
  2. Drug JSON files (medications) from raw/drugs/*.json
"""

import xml.etree.ElementTree as ET
import html
import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RAW_XML = DATA_DIR / "knowledge_docs" / "raw" / "mplus_topics.xml"
RAW_DRUGS = DATA_DIR / "knowledge_docs" / "raw" / "drugs"
OUTPUT_DIR = DATA_DIR / "knowledge_docs" / "processed"


# ── Health Topics XML ────────────────────────────────────────────────

def parse_health_topics(xml_path: Path = RAW_XML) -> list[dict]:
    """Parse health topics XML into a list of topic dicts."""
    if not xml_path.exists():
        logger.warning("XML not found at %s — skipping health topics", xml_path)
        return []

    tree = ET.parse(xml_path)
    root = tree.getroot()

    topics = []
    for el in root.findall("health-topic"):
        if el.get("language", "") != "English":
            continue

        title = el.get("title", "").strip()
        url = el.get("url", "")
        topic_id = el.get("id", "")

        summary_raw = el.findtext("full-summary", default="")
        summary = _clean_html(summary_raw)
        if not summary:
            continue

        also_called = [a.text.strip() for a in el.findall("also-called") if a.text]

        mesh_codes = []
        for mh in el.findall("mesh-heading"):
            desc = mh.find("descriptor")
            if desc is not None and desc.text:
                mesh_codes.append({"id": desc.get("id", ""), "name": desc.text.strip()})

        groups = [g.text.strip() for g in el.findall("group") if g.text]

        topics.append({
            "title": title,
            "url": url,
            "topic_id": topic_id,
            "summary": summary,
            "also_called": also_called,
            "mesh_codes": mesh_codes,
            "groups": groups,
            "doc_type": "health_topic",
        })

    logger.info("Parsed %d English health topics", len(topics))
    return topics


# ── Drug JSON Files ──────────────────────────────────────────────────

def parse_drug_files(drugs_dir: Path = RAW_DRUGS) -> list[dict]:
    """Parse drug JSON files into the same dict format as health topics."""
    if not drugs_dir.exists():
        logger.warning("Drugs dir not found at %s — skipping drugs", drugs_dir)
        return []

    drugs = []
    for jf in sorted(drugs_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read %s: %s", jf.name, e)
            continue

        title = data.get("title", data.get("drug_name", "Unknown Drug"))
        summary = data.get("summary", "")
        if not summary:
            continue

        drugs.append({
            "title": title,
            "url": data.get("url", ""),
            "summary": summary,
            "also_called": [data["drug_name"]] if data.get("drug_name") != title else [],
            "mesh_codes": [],
            "groups": ["Drugs and Supplements"],
            "doc_type": "drug",
        })

    logger.info("Parsed %d drug entries", len(drugs))
    return drugs


# ── Shared Helpers ───────────────────────────────────────────────────

def _clean_html(raw: str) -> str:
    """Unescape XML entities, strip HTML tags, normalize whitespace."""
    if not raw.strip():
        return ""
    unescaped = html.unescape(raw)
    soup = BeautifulSoup(unescaped, "html.parser")
    for li in soup.find_all("li"):
        li.insert_before("- ")
        li.append("\n")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def doc_to_text(doc: dict) -> str:
    """Convert a parsed doc dict into a text file string."""
    lines = [f"# {doc['title']}"]

    if doc.get("also_called"):
        lines.append(f"Also known as: {', '.join(doc['also_called'])}")

    if doc.get("doc_type") == "drug":
        lines.append("Type: Medication / Drug Information")

    lines.append("")
    lines.append(doc["summary"])
    lines.append("")

    if doc.get("url"):
        lines.append(f"Source: {doc['url']}")
    if doc.get("mesh_codes"):
        mesh_str = ", ".join(f"{m['name']} ({m['id']})" for m in doc["mesh_codes"])
        lines.append(f"MeSH: {mesh_str}")
    if doc.get("groups"):
        lines.append(f"Categories: {', '.join(doc['groups'])}")

    return "\n".join(lines)


def save_all(docs: list[dict], output_dir: Path = OUTPUT_DIR) -> int:
    """Save every doc as a .txt file. Returns count saved."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track slugs to avoid collisions between topics and drugs
    used_slugs = set()
    saved = 0

    for doc in docs:
        slug = re.sub(r"[^a-z0-9]+", "_", doc["title"].lower()).strip("_")

        # Prefix drug files to avoid name collision with health topics
        if doc.get("doc_type") == "drug":
            slug = f"drug_{slug}"

        # Handle duplicates
        base_slug = slug
        counter = 1
        while slug in used_slugs:
            slug = f"{base_slug}_{counter}"
            counter += 1
        used_slugs.add(slug)

        filepath = output_dir / f"{slug}.txt"
        filepath.write_text(doc_to_text(doc), encoding="utf-8")
        saved += 1

    return saved


# ── Main ─────────────────────────────────────────────────────────────

def run():
    """Full pipeline: parse health topics + drugs → save text files."""
    # Clear old processed files
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.txt"):
            f.unlink()

    topics = parse_health_topics()
    drugs = parse_drug_files()

    all_docs = topics + drugs
    count = save_all(all_docs)

    topic_count = len(topics)
    drug_count = len(drugs)

    print(f"\nDone.")
    print(f"  Health topics: {topic_count}")
    print(f"  Drug entries:  {drug_count}")
    print(f"  Total saved:   {count} files in {OUTPUT_DIR}")


if __name__ == "__main__":
    run()