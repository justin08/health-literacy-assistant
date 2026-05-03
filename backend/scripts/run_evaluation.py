"""Run the RAG pipeline evaluation across 30 medical terms.
Tests retrieval quality, readability, jargon, and faithfulness.
Outputs a summary report to stdout and a CSV to data/eval_results.csv.
"""

import sys
import csv
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.kb_retriever import Retriever
from app.services.evaluation import evaluate_explanation, score_readability, format_report
from app.services.safety import check_safety

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

# 30 test terms spanning conditions, medications, and lab results
TEST_TERMS = [
    # Conditions (10)
    {"term": "Diabetes mellitus type 2", "type": "condition", "expected_topic": "Diabetes"},
    {"term": "Hypertension", "type": "condition", "expected_topic": "Blood Pressure"},
    {"term": "Asthma", "type": "condition", "expected_topic": "Asthma"},
    {"term": "Coronary artery disease", "type": "condition", "expected_topic": "Coronary"},
    {"term": "Chronic kidney disease", "type": "condition", "expected_topic": "Kidney"},
    {"term": "Depression", "type": "condition", "expected_topic": "Depression"},
    {"term": "Rheumatoid arthritis", "type": "condition", "expected_topic": "Arthritis"},
    {"term": "Hypothyroidism", "type": "condition", "expected_topic": "Thyroid"},
    {"term": "Anemia", "type": "condition", "expected_topic": "Anemia"},
    {"term": "Atrial fibrillation", "type": "condition", "expected_topic": "Atrial"},

    # Medications (10)
    {"term": "Metformin 500 MG Oral Tablet", "type": "medication", "expected_topic": "Metformin"},
    {"term": "Lisinopril 10 MG", "type": "medication", "expected_topic": "Lisinopril"},
    {"term": "Atorvastatin 20 MG", "type": "medication", "expected_topic": "Atorvastatin"},
    {"term": "Ibuprofen 200 MG", "type": "medication", "expected_topic": "Ibuprofen"},
    {"term": "Omeprazole 20 MG", "type": "medication", "expected_topic": "Omeprazole"},
    {"term": "Amoxicillin 500 MG", "type": "medication", "expected_topic": "Amoxicillin"},
    {"term": "Sertraline 50 MG", "type": "medication", "expected_topic": "Sertraline"},
    {"term": "Albuterol inhaler", "type": "medication", "expected_topic": "Albuterol"},
    {"term": "Prednisone 5 MG", "type": "medication", "expected_topic": "Prednisone"},
    {"term": "Gabapentin 300 MG", "type": "medication", "expected_topic": "Gabapentin"},

    # Lab results / Observations (10)
    {"term": "Total Cholesterol: 215 mg/dL", "type": "observation", "expected_topic": "Cholesterol"},
    {"term": "Hemoglobin A1c: 7.2%", "type": "observation", "expected_topic": "A1C"},
    {"term": "Glucose: 140 mg/dL", "type": "observation", "expected_topic": "Glucose"},
    {"term": "Blood Urea Nitrogen: 25 mg/dL", "type": "observation", "expected_topic": "Kidney"},
    {"term": "Systolic Blood Pressure: 150 mmHg", "type": "observation", "expected_topic": "Blood Pressure"},
    {"term": "Triglycerides: 200 mg/dL", "type": "observation", "expected_topic": "Triglyceride"},
    {"term": "Creatinine: 1.5 mg/dL", "type": "observation", "expected_topic": "Kidney"},
    {"term": "Body Mass Index: 32 kg/m2", "type": "observation", "expected_topic": "Weight"},
    {"term": "Potassium: 5.5 mmol/L", "type": "observation", "expected_topic": "Potassium"},
    {"term": "Sodium: 130 mmol/L", "type": "observation", "expected_topic": "Sodium"},
]


def main():
    print("=" * 70)
    print("RAG Pipeline Evaluation — 30 Medical Terms")
    print("=" * 70)

    retriever = Retriever()
    if not retriever.ready:
        print("ERROR: Knowledge base not indexed. Run build_index.py first.")
        sys.exit(1)

    print(f"Knowledge base: {retriever.store.count()} chunks indexed\n")

    results = []
    retrieval_hits = 0
    total_score = 0

    for i, test in enumerate(TEST_TERMS, 1):
        term = test["term"]
        expected = test["expected_topic"].lower()

        # Test retrieval
        hits = retriever.retrieve(term, top_k=3)
        top_title = hits[0]["metadata"].get("title", "") if hits else ""
        top_score = hits[0]["score"] if hits else 0
        retrieval_match = expected in top_title.lower() if top_title else False

        if retrieval_match:
            retrieval_hits += 1

        # Get the retrieved context for faithfulness testing
        context = retriever.retrieve_as_context(term)

        # Score the retrieved text itself (since we may not have LLM)
        retrieved_text = hits[0]["text"] if hits else ""
        eval_scores = evaluate_explanation(retrieved_text, context) if retrieved_text else None

        result = {
            "term": term,
            "type": test["type"],
            "expected": test["expected_topic"],
            "top_result": top_title,
            "retrieval_score": round(top_score, 3),
            "retrieval_match": retrieval_match,
        }

        if eval_scores:
            result["fk_grade"] = eval_scores["readability"]["flesch_kincaid_grade"]
            result["reading_ease"] = eval_scores["readability"]["flesch_reading_ease"]
            result["jargon_count"] = eval_scores["jargon"]["total_jargon_found"]
            result["unexplained_jargon"] = len(eval_scores["jargon"]["unexplained_terms"])

        results.append(result)

        # Print progress
        match_icon = "✅" if retrieval_match else "❌"
        print(f"  [{i:2d}/30] {match_icon} {term[:45]:45s} → {top_title[:30]} ({top_score:.3f})")

    # Summary
    print(f"\n{'=' * 70}")
    print("RETRIEVAL SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total terms tested:  {len(TEST_TERMS)}")
    print(f"  Retrieval matches:   {retrieval_hits}/{len(TEST_TERMS)} ({100*retrieval_hits/len(TEST_TERMS):.0f}%)")

    # By type
    for term_type in ["condition", "medication", "observation"]:
        type_results = [r for r in results if r["type"] == term_type]
        type_hits = sum(1 for r in type_results if r["retrieval_match"])
        print(f"    {term_type:15s}: {type_hits}/{len(type_results)}")

    # Score distribution
    scores = [r["retrieval_score"] for r in results]
    print(f"\n  Score distribution:")
    print(f"    Mean:    {sum(scores)/len(scores):.3f}")
    print(f"    Min:     {min(scores):.3f}")
    print(f"    Max:     {max(scores):.3f}")
    print(f"    >0.5:    {sum(1 for s in scores if s > 0.5)}/{len(scores)}")

    # Readability summary (from retrieved text)
    fk_grades = [r["fk_grade"] for r in results if "fk_grade" in r]
    if fk_grades:
        print(f"\n  Readability (retrieved text):")
        print(f"    Mean FK grade:  {sum(fk_grades)/len(fk_grades):.1f}")
        print(f"    ≤ 8th grade:    {sum(1 for g in fk_grades if g <= 8)}/{len(fk_grades)}")

    # Save CSV
    output_path = Path("data/eval_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  Results saved to: {output_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
