"""Contrato comum para qualquer LLM usada pelo Radar."""
import json
import re
from dataclasses import dataclass
from typing import Protocol


class LLMError(RuntimeError):
    """Falha ao obter uma resposta utilizável da LLM."""


@dataclass(frozen=True)
class LLMResponse:
    data: dict  # JSON da resposta, já convertido em dicionário
    model: str  # nome do modelo que respondeu


class LLMClient(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate_json(self, prompt: str) -> LLMResponse: ...


def parse_json_object(text: str) -> dict:
    """Converte a resposta em dict. Aceita JSON puro ou dentro de cercas de código markdown."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("A resposta da LLM não contém um JSON válido.") from None
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError("A resposta da LLM não contém um JSON válido.") from exc
    if not isinstance(data, dict):
        raise LLMError("A resposta da LLM não é um objeto JSON.")
    return data