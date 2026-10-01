from abc import ABC, abstractmethod

import requests


class LLMClient(ABC):
    @abstractmethod
    def generate(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        """messages: [{'role': 'user'|'assistant', 'content': str}, ...]"""


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        import anthropic
        if not api_key:
            raise RuntimeError("Falta ANTHROPIC_API_KEY en el .env")
        self.client, self.model = anthropic.Anthropic(api_key=api_key), model

    def generate(self, system, messages, max_tokens=1024):
        r = self.client.messages.create(model=self.model, max_tokens=max_tokens,
                                        system=system, messages=messages)
        return "".join(b.text for b in r.content if b.type == "text")


class OpenAICompatClient(LLMClient):
    """Cualquier endpoint /chat/completions (OpenAI, Ollama, vLLM, LM Studio...)."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.url, self.key, self.model = base_url.rstrip("/") + "/chat/completions", api_key, model

    def generate(self, system, messages, max_tokens=1024):
        try:
            # timeout alto: la primera petición carga el modelo en memoria
            r = requests.post(self.url, timeout=300,
                              headers={"Authorization": f"Bearer {self.key}"},
                              json={"model": self.model, "max_tokens": max_tokens, "temperature": 0.2,
                                    "messages": [{"role": "system", "content": system}, *messages]})
            r.raise_for_status()
        except requests.ConnectionError:
            raise RuntimeError(f"No hay conexión con el LLM en {self.url}. ¿Está corriendo Ollama?")
        except requests.HTTPError as e:
            raise RuntimeError(f"El LLM respondió {e.response.status_code}: {e.response.text[:200]} "
                               f"(¿descargaste el modelo '{self.model}'?)")
        return r.json()["choices"][0]["message"]["content"]
