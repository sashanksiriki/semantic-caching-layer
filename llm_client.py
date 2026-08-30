"""
Where the actual model call happens. Defaults to a mock that simulates
LLM latency so you can demo the cache's speedup without needing an API
key. Flip USE_REAL_LLM=true in .env with a GROQ_API_KEY to hit a real
model instead -- the rest of the system (normalization, caching,
metrics) doesn't change at all. That's the point of isolating this in
its own module: swapping providers is a one-file change.

Provider priority when use_real_llm=True: Groq -> OpenAI -> mock.
"""
import hashlib
import time

from app.config import settings


def call_llm_mock(prompt: str) -> str:
    time.sleep(0.4)  # simulate real network + inference latency
    digest = hashlib.md5(prompt.encode()).hexdigest()[:8]
    return f"[mock LLM response] Answer to: '{prompt[:60]}' (ref={digest})"


def _call_groq(prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def _call_openai(prompt: str) -> str:
    import openai

    client = openai.OpenAI(api_key=settings.openai_api_key)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def call_llm(prompt: str) -> str:
    if settings.use_real_llm and settings.groq_api_key:
        return _call_groq(prompt)
    if settings.use_real_llm and settings.openai_api_key:
        return _call_openai(prompt)
    return call_llm_mock(prompt)
