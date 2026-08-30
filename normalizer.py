"""
Prompt normalization.

Two prompts that mean the same thing can differ in whitespace, casing,
or the specific date/number embedded in them ("What's the refund policy
for order 4471?" vs "...for order 8823?"). If you embed the raw text,
those get treated as different questions and you miss cache hits you
should be getting. Normalizing before embedding fixes that.

This is deliberately simple (regex-based) so it's fast and has zero
extra dependencies. In production you'd likely extend this with
domain-specific slot-filling (e.g. NER for names/entities).
"""
import re

_WHITESPACE = re.compile(r"\s+")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_NUMBER = re.compile(r"\b\d+\b")


def normalize_prompt(text: str) -> str:
    text = text.strip().lower()
    text = _WHITESPACE.sub(" ", text)
    text = _DATE.sub("<date>", text)
    text = _NUMBER.sub("<num>", text)
    return text
