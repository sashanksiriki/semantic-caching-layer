# Semantic Caching Layer

A backend service that sits in front of an LLM (Groq) and recognizes when a
new question means the same thing as one it's already answered — even if
it's worded completely differently — and reuses the old answer instead of
paying for a new AI call.

## Why I built this

Every AI-powered support tool pays per API call, and a large share of real
customer questions are the same handful of questions asked in different
words: "What's your return policy?", "Can I return this?", "Am I allowed to
send this back?" A naive setup treats all three as brand new questions and
pays for three separate AI calls. This project fixes that: it understands
*meaning*, not just exact wording, and only calls the AI when a question is
genuinely new.

## What it does

- Takes any incoming question and checks whether a semantically similar
  question has already been answered
- If yes, returns the existing answer instantly, at no additional cost
- If no, calls the AI, gets a real answer, and remembers it for next time
- Automatically refuses to cache anything where the right answer changes
  moment to moment (e.g. "what's my account balance", "what's the weather
  today") — accuracy is never sacrificed for cost savings
- Tracks its own performance: hit rate, average AI response time, and
  measured time saved — so the savings are a real number, not a guess
- Protected behind an API key and rate limiting, like any real backend
  service

## Results (from my own test run)

| Metric | Value |
|---|---|
| Cache hit rate | 94.7% (18 hits / 19 cacheable questions) |
| Average fresh AI response time | 7.1s |
| Total measured time saved | 118.4s across the test session |
| Non-cacheable questions correctly blocked | 9 |

*(Screenshots of these results below.)*

![Metrics screenshot](docs/metrics.png)
![Semantic match example](docs/match-example.png)

Hit rate climbs the more real traffic the cache has seen — a cold cache on
day one looks unremarkable; the same system after real usage looks very
different, since it's only ever answering genuinely new questions from
scratch.