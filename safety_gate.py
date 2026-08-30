"""
Safety gate: decides whether a prompt is even allowed to touch the cache.

Some queries should NEVER be served from cache, no matter how similar
they look to a past prompt:
  - anything time-relative ("what's the weather today", "latest news")
  - anything account/user-specific (would leak one user's cached
    answer to another user)

This is a cheap regex pass. In a real system you'd likely swap this for
a small classifier or a rules engine tied to your query taxonomy, but
the interface (`is_cacheable(prompt) -> bool`) stays the same.
"""
import re

_NON_CACHEABLE_PATTERNS = [
    r"\btoday\b",
    r"\bnow\b",
    r"\bcurrent(ly)?\b",
    r"\blatest\b",
    r"\bthis (week|month|year)\b",
    r"\bstock price\b",
    r"\bweather\b",
    r"\bmy (account|order|password|balance|ssn|social security)\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _NON_CACHEABLE_PATTERNS]


def is_cacheable(prompt: str) -> bool:
    return not any(p.search(prompt) for p in _COMPILED)
