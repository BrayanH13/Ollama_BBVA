from app.config import Settings
from app.llm.clients import AnthropicClient, LLMClient, OpenAICompatClient


def create_llm(cfg: Settings) -> LLMClient:
    if cfg.llm_provider == "ollama":
        # Ollama expone una API compatible con OpenAI; la API key es un valor ficticio.
        return OpenAICompatClient(cfg.ollama_base_url, "ollama", cfg.ollama_model)
    if cfg.llm_provider == "openai":
        return OpenAICompatClient(cfg.openai_base_url, cfg.openai_api_key, cfg.openai_model)
    if cfg.llm_provider == "anthropic":
        return AnthropicClient(cfg.anthropic_api_key, cfg.anthropic_model)
    raise ValueError(f"LLM_PROVIDER desconocido: {cfg.llm_provider} (usa ollama | openai | anthropic)")
