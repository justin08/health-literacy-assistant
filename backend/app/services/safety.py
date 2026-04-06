"""Safety checks for LLM-generated explanations.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Phrases that suggest the LLM is giving direct medical advice
ADVICE_PATTERNS = [
    r"\byou should (take|stop|increase|decrease|change)\b",
    r"\bstop taking\b",
    r"\bstart taking\b",
    r"\bi recommend\b",
    r"\byou need to (take|start|stop)\b",
    r"\bdo not take\b",
    r"\byou must\b",
    r"\bswitch to\b",
    r"\bincrease your dose\b",
    r"\bdecrease your dose\b",
]

# The explanation should end with a doctor reminder
DOCTOR_PHRASES = [
    "doctor", "nurse", "healthcare provider",
    "health care provider", "medical professional",
    "pharmacist", "provider",
]

DISCLAIMER = (
    "\n\nThis is general health information, not medical advice. "
    "Please talk to your doctor or nurse if you have questions."
)


def check_safety(explanation: str) -> dict:
    """Run safety checks on an LLM-generated explanation.

    Returns a dict with:
      - text: the (possibly modified) explanation
      - warnings: list of issues found
      - passed: True if no critical issues
    """
    warnings = []
    text = explanation

    # Check for direct medical advice
    advice_found = _check_advice(text)
    if advice_found:
        warnings.append(f"Possible medical advice detected: {advice_found}")
        logger.warning("Safety: medical advice pattern found — '%s'", advice_found)

    # Check for doctor reminder at the end
    if not _has_doctor_reminder(text):
        warnings.append("Missing doctor/provider reminder — disclaimer added")
        text = text.rstrip() + DISCLAIMER

    # Check for extremely short or empty responses
    if len(text.strip()) < 30:
        warnings.append("Response too short — may be incomplete")

    passed = len([w for w in warnings if "medical advice" in w]) == 0

    if warnings:
        logger.info("Safety check: %d warnings — %s", len(warnings), "; ".join(warnings))

    return {
        "text": text,
        "warnings": warnings,
        "passed": passed,
    }


def _check_advice(text: str) -> str:
    """Return the first medical advice pattern found, or empty string."""
    lower = text.lower()
    for pattern in ADVICE_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            return match.group(0)
    return ""


def _has_doctor_reminder(text: str) -> bool:
    """Check if the last 200 chars mention a doctor/provider."""
    tail = text[-200:].lower()
    return any(phrase in tail for phrase in DOCTOR_PHRASES)