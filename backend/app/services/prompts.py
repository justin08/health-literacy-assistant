"""Prompt templates for the RAG pipeline.
"""

SYSTEM_PROMPT = """\
You are a patient health literacy assistant. Your job is to help \
patients understand their medical records by translating clinical \
language into clear, simple explanations.

RULES:
1. Write at a 6th-to-8th grade reading level. Avoid medical jargon.
2. If you use a medical term, immediately define it in parentheses.
3. ONLY use information from the provided reference material. If the \
   reference material does not cover something, say so honestly.
4. Never diagnose, recommend treatment, or give medical advice.
5. Be reassuring but honest. Do not minimize or exaggerate.
6. Use short sentences and short paragraphs.
7. End by reminding the patient to talk to their doctor or nurse \
   if they have questions or concerns.\
"""

OBSERVATION_PROMPT = """\
A patient is viewing this lab result from their medical record:

--- Clinical Data ---
Test: {display}
Result: {value} {unit}
Date: {date}
{flag_line}
---

Using ONLY the reference material below, explain this result in \
plain language.

--- Reference Material ---
{context}
---

Structure your answer as:
1. What was tested — one sentence explaining the test simply.
2. The result — state the number and whether it looks normal or not.
3. What this means — a brief plain-language explanation.
4. Reminder to discuss with their doctor if they have questions.\
"""

CONDITION_PROMPT = """\
A patient is viewing this diagnosis from their medical record:

--- Clinical Data ---
Condition: {display}
Status: {status}
Date recorded: {date}
---

Using ONLY the reference material below, explain this condition in \
plain language.

--- Reference Material ---
{context}
---

Structure your answer as:
1. What this condition is — a simple explanation.
2. What the status means (active, resolved, etc.).
3. Key things to know from the reference material.
4. Reminder to discuss with their doctor if they have questions.\
"""

MEDICATION_PROMPT = """\
A patient is viewing this prescription from their medical record:

--- Clinical Data ---
Medication: {display}
Instructions: {instructions}
Date prescribed: {date}
---

Using ONLY the reference material below, explain this medication in \
plain language.

--- Reference Material ---
{context}
---

Structure your answer as:
1. What this medication is and what it does, in simple terms.
2. How to take it — restate the instructions in plain language.
3. Important things to know from the reference material.
4. Reminder to ask their doctor or pharmacist if they have questions.\
"""

GENERAL_PROMPT = """\
A patient wants to understand this medical term:

--- Term ---
{term}
{context_line}
---

Using ONLY the reference material below, explain this in plain \
language that a regular person can understand.

--- Reference Material ---
{context}
---

Keep your explanation to 2-3 short paragraphs. Remind the patient \
to talk to their doctor if they have questions.\
"""


def build_observation_prompt(display: str, value: float, unit: str,
                              date: str, flag: str, context: str) -> str:
    flag_line = f"Flag: {flag} (abnormal)" if flag else ""
    return OBSERVATION_PROMPT.format(
        display=display, value=value, unit=unit,
        date=date, flag_line=flag_line, context=context,
    )


def build_condition_prompt(display: str, status: str,
                            date: str, context: str) -> str:
    return CONDITION_PROMPT.format(
        display=display, status=status,
        date=date, context=context,
    )


def build_medication_prompt(display: str, instructions: str,
                             date: str, context: str) -> str:
    return MEDICATION_PROMPT.format(
        display=display, instructions=instructions,
        date=date, context=context,
    )


def build_general_prompt(term: str, context: str,
                          patient_context: str = "") -> str:
    context_line = f"Patient context: {patient_context}" if patient_context else ""
    return GENERAL_PROMPT.format(
        term=term, context_line=context_line, context=context,
    )