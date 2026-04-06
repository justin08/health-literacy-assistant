"""Evaluate the quality of generated plain-language explanations.
"""

import re
import logging
import textstat

logger = logging.getLogger(__name__)

TARGET_FK_GRADE = 8.0
TARGET_READING_EASE = 60.0

# Common medical jargon that should be explained or avoided
JARGON_TERMS = [
    "hypertension", "hyperlipidemia", "hypercholesterolemia",
    "tachycardia", "bradycardia", "arrhythmia",
    "dyspnea", "edema", "ischemia", "infarction",
    "thrombosis", "embolism", "stenosis",
    "nephropathy", "neuropathy", "retinopathy",
    "hematuria", "proteinuria", "glycosuria",
    "leukocytosis", "thrombocytopenia", "anemia",
    "hepatic", "renal", "pulmonary", "cardiac",
    "subcutaneous", "intravenous", "intramuscular",
    "etiology", "pathogenesis", "prognosis",
    "contraindicated", "prophylaxis", "idiopathic",
    "benign", "malignant", "metastasis",
    "bilateral", "unilateral", "proximal", "distal",
    "acute", "chronic", "comorbidity",
    "hemoglobin", "platelet", "creatinine",
    "lipid", "triglyceride", "bilirubin",
]


def evaluate_explanation(explanation: str, context: str = "") -> dict:
    """Run all evaluation metrics on an explanation.

    Returns a dict with scores, flags, and an overall assessment.
    """
    readability = score_readability(explanation)
    jargon = detect_jargon(explanation)
    faithfulness = check_faithfulness(explanation, context) if context else None

    overall_pass = (
        readability["meets_grade_target"]
        and len(jargon["unexplained_terms"]) <= 2
    )

    result = {
        "readability": readability,
        "jargon": jargon,
        "overall_pass": overall_pass,
    }

    if faithfulness is not None:
        result["faithfulness"] = faithfulness
        if not faithfulness["grounded"]:
            result["overall_pass"] = False

    return result


def score_readability(text: str) -> dict:
    """Compute readability metrics."""
    fk_grade = textstat.flesch_kincaid_grade(text)
    fre = textstat.flesch_reading_ease(text)

    return {
        "flesch_kincaid_grade": round(fk_grade, 1),
        "flesch_reading_ease": round(fre, 1),
        "meets_grade_target": fk_grade <= TARGET_FK_GRADE,
        "meets_ease_target": fre >= TARGET_READING_EASE,
    }


def detect_jargon(text: str) -> dict:
    """Find medical jargon that appears without explanation.

    A term is "explained" if it's followed by parentheses or
    a phrase like "which means" or "this is called".
    """
    lower = text.lower()
    found = []
    unexplained = []

    for term in JARGON_TERMS:
        if term in lower:
            found.append(term)
            if not _is_explained(lower, term):
                unexplained.append(term)

    return {
        "total_jargon_found": len(found),
        "unexplained_terms": unexplained,
        "all_terms_found": found,
    }


def _is_explained(text: str, term: str) -> bool:
    """Check if a jargon term is followed by an explanation."""
    idx = text.find(term)
    if idx == -1:
        return False

    # Look at the 100 chars after the term
    after = text[idx + len(term):idx + len(term) + 100]

    explanation_signals = [
        "(", "which means", "which is", "this means",
        "that means", "also called", "also known as",
        "in other words", ", meaning", ", or",
    ]
    return any(signal in after for signal in explanation_signals)


def check_faithfulness(explanation: str, context: str) -> dict:
    """Basic faithfulness check — are key claims grounded in context?

    Extracts factual-looking statements from the explanation and
    checks if similar content appears in the retrieved context.
    Simple overlap-based approach, not semantic.
    """
    # Extract key phrases (numbers, percentages, ranges)
    claims = re.findall(
        r'\d+\.?\d*\s*(?:%|mg|mg/dL|mmol|mmHg|kg|cm|units?)',
        explanation, re.IGNORECASE,
    )

    context_lower = context.lower()
    grounded_claims = []
    ungrounded_claims = []

    for claim in claims:
        # Check if the number appears in context
        number = re.search(r'\d+\.?\d*', claim)
        if number and number.group() in context_lower:
            grounded_claims.append(claim)
        else:
            ungrounded_claims.append(claim)

    grounded = len(ungrounded_claims) == 0 or len(claims) == 0

    return {
        "grounded": grounded,
        "total_claims": len(claims),
        "grounded_claims": len(grounded_claims),
        "ungrounded_claims": ungrounded_claims,
    }


def format_report(scores: dict) -> str:
    """Pretty-print evaluation results."""
    r = scores["readability"]
    j = scores["jargon"]

    lines = [
        "Evaluation Report",
        "=" * 40,
        f"{'✅' if r['meets_grade_target'] else '⚠️'} Flesch-Kincaid Grade: {r['flesch_kincaid_grade']} (target ≤ {TARGET_FK_GRADE})",
        f"{'✅' if r['meets_ease_target'] else '⚠️'} Reading Ease: {r['flesch_reading_ease']} (target ≥ {TARGET_READING_EASE})",
        f"{'✅' if len(j['unexplained_terms']) <= 2 else '⚠️'} Jargon: {j['total_jargon_found']} found, {len(j['unexplained_terms'])} unexplained",
    ]

    if j["unexplained_terms"]:
        lines.append(f"   Unexplained: {', '.join(j['unexplained_terms'])}")

    if "faithfulness" in scores:
        f = scores["faithfulness"]
        lines.append(f"{'✅' if f['grounded'] else '⚠️'} Faithfulness: {f['grounded_claims']}/{f['total_claims']} claims grounded")
        if f["ungrounded_claims"]:
            lines.append(f"   Ungrounded: {', '.join(f['ungrounded_claims'])}")

    status = "PASS ✅" if scores["overall_pass"] else "NEEDS REVIEW ⚠️"
    lines.append(f"\nOverall: {status}")

    return "\n".join(lines)