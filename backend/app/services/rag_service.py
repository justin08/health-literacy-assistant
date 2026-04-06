import logging
import os
import textstat

from app.services.kb_retriever import Retriever
from app.services.prompts import (
    SYSTEM_PROMPT,
    build_observation_prompt,
    build_condition_prompt,
    build_medication_prompt,
    build_general_prompt,
)

logger = logging.getLogger(__name__)

_openai_available = False
try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    logger.warning("openai package not installed")


class RAGService:
    def __init__(self):
        self.retriever = None
        self.llm = None
        self.ready = False
        self._init()

    def _init(self):
        try:
            self.retriever = Retriever()

            api_key = os.getenv("OPENAI_API_KEY", "")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
            self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

            if api_key and _openai_available:
                self.llm = OpenAI(api_key=api_key)
                logger.info("LLM ready: OpenAI %s", self.model)
            else:
                if not api_key:
                    logger.warning("No OPENAI_API_KEY — LLM generation disabled")
                if not _openai_available:
                    logger.warning("openai package not installed")

            if self.retriever.ready:
                self.ready = True
                logger.info("RAG ready — %d chunks indexed", self.retriever.store.count())
            else:
                logger.warning("RAG not ready — knowledge base empty")

        except Exception as e:
            logger.error("RAG init failed: %s", e)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI and return the response text."""
        if not self.llm:
            return ""

        response = self.llm.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def explain(self, term: str, context: str = "") -> dict:
        """Explain a medical term using RAG.

        Main entry point called by explain_routes.py.
        Same return format as the original.
        """
        if not self.ready:
            return self._fallback_explain(term)

        try:
            return self._rag_explain(term, context)
        except Exception as e:
            logger.error("RAG explain failed: %s", e)
            return self._fallback_explain(term)

    def explain_observation(self, display: str, value: float,
                            unit: str, date: str, flag: str = "") -> dict:
        """Explain a lab result with full clinical context."""
        query = f"{display}: {value} {unit}"
        if flag:
            query += f". Interpretation: {flag}"

        context = self.retriever.retrieve_as_context(query)
        prompt = build_observation_prompt(display, value, unit, date, flag, context)
        return self._generate_and_score(prompt)

    def explain_condition(self, display: str, status: str, date: str) -> dict:
        """Explain a diagnosis."""
        query = f"Diagnosis: {display}. Status: {status}"
        context = self.retriever.retrieve_as_context(query)
        prompt = build_condition_prompt(display, status, date, context)
        return self._generate_and_score(prompt)

    def explain_medication(self, display: str, instructions: str, date: str) -> dict:
        """Explain a prescription."""
        query = f"Medication: {display}. {instructions}"
        context = self.retriever.retrieve_as_context(query)
        prompt = build_medication_prompt(display, instructions, date, context)
        return self._generate_and_score(prompt)

    def _rag_explain(self, term: str, patient_context: str) -> dict:
        """General-purpose explain for the /api/explain endpoint."""
        context = self.retriever.retrieve_as_context(term)
        prompt = build_general_prompt(term, context, patient_context)
        result = self._generate_and_score(prompt)

        # Add source URLs from retrieval
        results = self.retriever.retrieve(term, top_k=3)
        sources = []
        for r in results:
            url = r["metadata"].get("source_url", "")
            title = r["metadata"].get("title", "")
            if url:
                sources.append(url)
            elif title:
                sources.append(title)
        result["sources"] = sources if sources else ["MedlinePlus"]

        return result

    def _generate_and_score(self, user_prompt: str) -> dict:
        """Call LLM, score readability, return formatted result."""
        if not self.llm:
            return self._fallback_explain(user_prompt[:50])

        explanation = self._call_llm(SYSTEM_PROMPT, user_prompt)
        score = textstat.flesch_kincaid_grade(explanation)

        return {
            "plain_language": explanation,
            "sources": ["MedlinePlus"],
            "readability_score": round(score, 1),
        }

    def _fallback_explain(self, term: str) -> dict:
        """Fallback when LLM is unavailable — returns raw retrieved text."""
        if self.retriever and self.retriever.ready:
            results = self.retriever.retrieve(term, top_k=1)
            if results and results[0]["score"] > 0.4:
                text = results[0]["text"]
                lines = text.split("\n\n", 1)
                body = lines[1] if len(lines) > 1 else text
                if len(body) > 500:
                    body = body[:500].rsplit(".", 1)[0] + "."

                return {
                    "plain_language": body,
                    "sources": ["MedlinePlus"],
                    "readability_score": round(textstat.flesch_kincaid_grade(body), 1),
                }

        return {
            "plain_language": (
                f"'{term}' is a medical term. Ask your doctor or "
                "nurse to explain what this means for you."
            ),
            "sources": ["General"],
            "readability_score": 6.0,
        }