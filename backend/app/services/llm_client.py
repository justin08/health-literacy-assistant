"""LLM client for generating plain-language explanations.
"""

import logging
import os

logger = logging.getLogger(__name__)

_anthropic_available = False
_openai_available = False

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    pass

try:
    import openai
    _openai_available = True
except ImportError:
    pass


class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.ready = False
        self._client = None

        # Anthropic
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

        # OpenAI
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Shared
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

        self._init_client()

    def _init_client(self):
        """Try configured provider first, then fallback to the other."""
        if self.provider == "anthropic":
            if self._try_anthropic() or self._try_openai():
                return
        else:
            if self._try_openai() or self._try_anthropic():
                return

        logger.warning("No LLM API key configured — generation disabled")

    def _try_anthropic(self) -> bool:
        if self.anthropic_key and _anthropic_available:
            self._client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.provider = "anthropic"
            self.ready = True
            logger.info("LLM ready: Anthropic %s", self.anthropic_model)
            return True
        return False

    def _try_openai(self) -> bool:
        if self.openai_key and _openai_available:
            self._client = openai.OpenAI(api_key=self.openai_key)
            self.provider = "openai"
            self.ready = True
            logger.info("LLM ready: OpenAI %s", self.openai_model)
            return True
        return False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the response text."""
        if not self.ready:
            return self._no_llm_fallback()

        try:
            if self.provider == "anthropic":
                return self._call_anthropic(system_prompt, user_prompt)
            else:
                return self._call_openai(system_prompt, user_prompt)
        except Exception as e:
            logger.error("LLM call failed (%s): %s", self.provider, e)
            return self._error_fallback()

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self.anthropic_model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.openai_model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def _no_llm_fallback(self) -> str:
        return (
            "Plain-language explanation is not available right now "
            "(no AI service configured). Please ask your doctor or "
            "nurse to explain this to you."
        )

    def _error_fallback(self) -> str:
        return (
            "We had trouble generating an explanation. "
            "Please try again or ask your doctor or nurse."
        )

    def get_status(self) -> dict:
        """Return current LLM configuration info."""
        model = self.anthropic_model if self.provider == "anthropic" else self.openai_model
        return {
            "provider": self.provider if self.ready else "none",
            "model": model if self.ready else "none",
            "ready": self.ready,
        }