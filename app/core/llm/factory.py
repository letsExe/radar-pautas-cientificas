from app.core.config import settings
from app.core.llm.base import LLMClient, LLMError
from app.core.llm.gemini_client import GeminiClient


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Cria o cliente do provedor pedido (ou o definido em LLM_PROVIDER no .env)."""
    provider = (provider or settings.llm_provider).lower()
    if provider == "gemini":
        return GeminiClient(
            settings.gemini_api_key, settings.gemini_model, settings.llm_timeout_seconds
        )
    raise LLMError(f"Provedor de LLM desconhecido: '{provider}'. Disponíveis: gemini.")