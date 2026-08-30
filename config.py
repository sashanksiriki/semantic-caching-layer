"""
Centralized configuration. Everything tunable about the cache's behavior
lives here so you're not hunting through files to change a threshold.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    embedding_model: str = "all-MiniLM-L6-v2"

    # Cosine similarity cutoff for treating two prompts as "the same question".
    # Higher = safer (fewer wrong cache hits), lower = more cache hits but riskier.
    similarity_threshold: float = 0.92

    # How long a cache entry stays valid before it's treated as stale.
    cache_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days

    # Hard cap on cache size. Past this, least-recently-used entries are evicted.
    max_cache_size: int = 5000

    chroma_persist_dir: str = "./cache_db"

    # Toggle between the built-in mock LLM (no API key needed, good for demos)
    # and a real call. Groq is checked first, then OpenAI, then falls back
    # to the mock if neither key is set.
    use_real_llm: bool = False
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    openai_api_key: str = ""

    # --- Security / ops ---
    # Simple shared-secret auth. Every request must send this in the
    # X-API-Key header. This is intentionally basic (not OAuth/JWT) --
    # good enough for an internal service or a demo, not a public API.
    api_key: str = ""

    # Requests allowed per client IP per minute on /query.
    rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
