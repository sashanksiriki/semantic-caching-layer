from pydantic import BaseModel


class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    response: str
    cache_hit: bool
    cacheable: bool
    similarity: float | None = None
