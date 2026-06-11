from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class RecSource(str, Enum):
    collaborative = "collaborative"
    content = "content"
    graph = "graph"
    hybrid = "hybrid"
    hot = "hot"
    cold_start = "cold_start"
    serendipity = "serendipity"


class RecommendItem(BaseModel):
    book_id: str
    score: float
    source: RecSource
    reason: Optional[str] = None


class RecommendResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendItem]
    total_count: int
    used_strategy: str


class WeeklyStats(BaseModel):
    week_start: str
    click_through_rate: float
    completion_rate: float
    collection_rate: float
    diversity_index: float
    total_impressions: int
    total_clicks: int
