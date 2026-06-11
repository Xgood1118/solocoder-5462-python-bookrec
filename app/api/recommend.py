from fastapi import APIRouter, HTTPException
from typing import List

from app.models.rec import RecommendResponse, RecommendItem, WeeklyStats
from app.storage.memory_store import get_storage
from app.rec.hybrid import get_hybrid_recommender
from app.rec.collaborative import get_collaborative_filtering
from app.rec.content_based import get_content_recommender
from app.rec.knowledge_graph import get_graph_recommender
from app.feedback.manager import get_feedback_manager
from app.abtest.manager import get_abtest_manager

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/{user_id}", response_model=RecommendResponse)
def get_recommendations(user_id: str, top_n: int = 20, ab_test: bool = False):
    hybrid_rec = get_hybrid_recommender()
    feedback = get_feedback_manager()

    feedback.record_impression()

    if ab_test:
        abtest = get_abtest_manager()
        group = abtest.assign_user_group(user_id)
        abtest.record_group_metric(group, "impressions", 1)

    items, strategy = hybrid_rec.recommend(user_id, top_n=top_n)

    diversity_index = hybrid_rec.calculate_diversity_index(items)

    return RecommendResponse(
        user_id=user_id,
        recommendations=items,
        total_count=len(items),
        used_strategy=f"{strategy}_diversity_{diversity_index:.2f}",
    )


@router.get("/{user_id}/collaborative", response_model=List[RecommendItem])
def get_collab_recommendations(user_id: str, top_n: int = 20):
    cf = get_collaborative_filtering()
    scores = cf.recommend(user_id, top_n=top_n)
    return [
        RecommendItem(book_id=bid, score=score, source="collaborative")
        for bid, score in scores
    ]


@router.get("/{user_id}/content", response_model=List[RecommendItem])
def get_content_recommendations(user_id: str, top_n: int = 20):
    content_rec = get_content_recommender()
    scores = content_rec.recommend(user_id, top_n=top_n)
    return [
        RecommendItem(book_id=bid, score=score, source="content")
        for bid, score in scores
    ]


@router.get("/{user_id}/graph", response_model=List[RecommendItem])
def get_graph_recommendations(user_id: str, top_n: int = 20):
    graph_rec = get_graph_recommender()
    scores = graph_rec.recommend(user_id, top_n=top_n)
    return [
        RecommendItem(book_id=bid, score=score, source="graph")
        for bid, score in scores
    ]


@router.get("/hot/list", response_model=List[RecommendItem])
def get_hot(top_n: int = 50):
    hybrid_rec = get_hybrid_recommender()
    return hybrid_rec.get_hot_books(top_n)


@router.get("/cold-start/tags", response_model=List[str])
def get_cold_start_tags():
    graph_rec = get_graph_recommender()
    top_tags = sorted(
        graph_rec.pagerank_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    return [tag for tag, _ in top_tags]


@router.get("/stats/weekly", response_model=WeeklyStats)
def get_weekly_stats():
    feedback = get_feedback_manager()
    stats = feedback.get_weekly_stats()
    return WeeklyStats(
        week_start=stats["week_start"],
        click_through_rate=stats["click_through_rate"],
        completion_rate=stats["completion_rate"],
        collection_rate=stats["collection_rate"],
        diversity_index=0.0,
        total_impressions=stats["impressions"],
        total_clicks=stats["clicks"],
    )


@router.post("/refresh")
def refresh_models():
    hybrid_rec = get_hybrid_recommender()
    hybrid_rec.refresh_all()
    return {"status": "ok", "message": "All models refreshed"}
