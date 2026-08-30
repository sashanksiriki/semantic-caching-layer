"""
API layer. This is the request pipeline every prompt goes through:

    request
      -> auth (X-API-Key header)       (reject if no/wrong key set)
      -> rate limit                    (per-IP requests/minute cap)
      -> safety_gate.is_cacheable()    (should this ever be cached?)
      -> normalizer.normalize_prompt() (strip noise before embedding)
      -> cache_store.lookup()          (semantic search + threshold + TTL)
      -> [HIT]  return cached response
      -> [MISS] llm_client.call_llm() -> cache_store.add() -> return
      -> metrics recorded at every branch
"""
from fastapi import Depends, FastAPI, Header, HTTPException, Request
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.cache_store import cache
from app.config import settings
from app.llm_client import call_llm
from app.metrics import metrics
from app.normalizer import normalize_prompt
from app.safety_gate import is_cacheable
from app.schemas import QueryRequest, QueryResponse

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Semantic Caching Layer", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """
    Shared-secret auth. If API_KEY is unset in .env, auth is skipped --
    handy for local dev, but you should always set it before deploying
    this anywhere reachable off your own machine.
    """
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(require_api_key)])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def query(request: Request, req: QueryRequest) -> QueryResponse:
    start = time.perf_counter()

    if not is_cacheable(req.prompt):
        metrics.record_blocked()
        response = call_llm(req.prompt)
        return QueryResponse(response=response, cache_hit=False, cacheable=False)

    normalized = normalize_prompt(req.prompt)
    hit = cache.lookup(normalized)

    if hit:
        metrics.record_hit(time.perf_counter() - start)
        return QueryResponse(
            response=hit["response"],
            cache_hit=True,
            cacheable=True,
            similarity=hit["similarity"],
        )

    response = call_llm(req.prompt)
    cache.add(normalized, req.prompt, response)
    metrics.record_miss(time.perf_counter() - start)
    return QueryResponse(response=response, cache_hit=False, cacheable=True)


@app.get("/metrics")
def get_metrics() -> dict:
    return metrics.snapshot()


@app.get("/cache/stats")
def cache_stats() -> dict:
    return cache.stats()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
