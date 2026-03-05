from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Tuple


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    collection: str = Field(..., description="Collection name: Landmarks, Movies, or Science")
    limit: int = Field(default=5, ge=1, le=20, description="Number of results per search type")


class BM25Result(BaseModel):
    title: str
    description: str
    score: float
    properties: Dict[str, Any] = {}


class SemanticResult(BaseModel):
    title: str
    description: str
    distance: Optional[float] = None
    certainty: Optional[float] = None
    properties: Dict[str, Any] = {}


class VectorPoint(BaseModel):
    title: str
    vector_2d: Tuple[float, float]
    certainty: Optional[float] = None
    distance: Optional[float] = None
    country: Optional[str] = None


class SearchTiming(BaseModel):
    bm25_ms: float
    semantic_ms: float


class DualSearchResponse(BaseModel):
    query: str
    collection: str
    bm25: List[BM25Result]
    semantic: List[SemanticResult]
    timing: SearchTiming
    query_terms: List[str] = []


class HybridResult(BaseModel):
    title: str
    description: str
    score: Optional[float] = None
    certainty: Optional[float] = None
    distance: Optional[float] = None
    properties: Dict[str, Any] = {}


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str
    limit: int = Field(default=10, ge=1, le=20)
    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="0=pure BM25, 1=pure semantic")


class HybridSearchResponse(BaseModel):
    query: str
    collection: str
    results: List[HybridResult]
    alpha: float
    hybrid_ms: float
