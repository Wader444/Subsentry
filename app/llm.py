"""LLM helper — rephrases wording only, NEVER sets scores.

Default provider ``"template"`` returns the caller's template text
unchanged (no network, no key needed). With another provider configured
(``LLM_PROVIDER`` + ``LLM_API_KEY``), it POSTs to ``LLM_BASE_URL`` and
returns the model's rephrasing; on ANY failure it returns the template
text instead of raising.
"""
import logging

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:  # pragma: no cover - requests is in requirements
    requests = None


def generate(prompt: str, context: str = "") -> str:
    """Return rephrased wording for ``prompt`` (template text by default)."""
    if settings.LLM_PROVIDER == "template" or not settings.LLM_API_KEY:
        return prompt
    if requests is None:
        logger.warning("requests not installed; falling back to template text")
        return prompt
    try:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        response = requests.post(
            settings.LLM_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": messages,
                "temperature": 0.3,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return text.strip() if isinstance(text, str) else prompt
    except Exception as exc:  # noqa: BLE001 - any LLM failure -> template
        logger.warning("LLM call failed (%s); falling back to template text", exc)
        return prompt
