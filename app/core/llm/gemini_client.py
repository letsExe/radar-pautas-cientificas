import time

import requests

from app.core.llm.base import LLMError, LLMResponse, parse_json_object

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
RETRY_STATUS = (429, 500, 502, 503, 504)


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout: int = 90, retries: int = 4) -> None:
        if not api_key:
            raise LLMError("GEMINI_API_KEY não definida. Preencha o arquivo .env.")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._retries = retries

    @property
    def model_name(self) -> str:
        return self._model

    def generate_json(self, prompt: str) -> LLMResponse:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        }
        data = self._post(body)
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"Resposta inesperada do Gemini: {str(data)[:300]}") from None
        return LLMResponse(data=parse_json_object(text), model=self._model)

    def _post(self, body: dict) -> dict:
        url = f"{BASE_URL}/{self._model}:generateContent"
        # A chave vai no cabeçalho (não na URL), para não aparecer em mensagens de erro.
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}
        last_error = ""
        for attempt in range(self._retries):
            try:
                response = requests.post(url, headers=headers, json=body, timeout=self._timeout)
            except requests.RequestException as exc:
                last_error = type(exc).__name__
            else:
                if response.ok:
                    return response.json()
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                if response.status_code not in RETRY_STATUS:
                    break  # erro nosso (chave, modelo, pedido inválido): repetir não adianta
            time.sleep(2 ** (attempt + 1))
        raise LLMError(f"Falha ao consultar o Gemini: {last_error}")