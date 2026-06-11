from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from app.models.feedback import UserFeedback, FeedbackType, FeedbackAggregate
from app.feedback.manager import get_feedback_manager
from app.storage.memory_store import get_storage

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    user_id: str
    book_id: str
    feedback_type: FeedbackType
    rec_source: str | None = None


@router.post("")
def submit_feedback(req: FeedbackRequest):
    try:
        storage = get_storage()
        if not storage.get_user(req.user_id):
            raise HTTPException(status_code=404, detail="User not found")
        if not storage.get_book(req.book_id):
            raise HTTPException(status_code=404, detail="Book not found")

        feedback_mgr = get_feedback_manager()
        fb = UserFeedback(
            user_id=req.user_id,
            book_id=req.book_id,
            feedback_type=req.feedback_type,
            rec_source=req.rec_source,
        )
        feedback_mgr.add_feedback(fb)

        return {"status": "ok", "message": "Feedback recorded", "feedback_type": req.feedback_type.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@router.get("/{user_id}/summary", response_model=FeedbackAggregate)
def get_feedback_summary(user_id: str):
    feedback_mgr = get_feedback_manager()
    return feedback_mgr.get_user_feedback_summary(user_id)


@router.get("/{user_id}/disliked-tags")
def get_disliked_tags(user_id: str):
    feedback_mgr = get_feedback_manager()
    return {
        "user_id": user_id,
        "disliked_tags": dict(feedback_mgr.disliked_tags.get(user_id, {})),
    }


@router.post("/{user_id}/click")
def record_click(user_id: str):
    feedback_mgr = get_feedback_manager()
    feedback_mgr.record_click()
    return {"status": "ok"}


@router.post("/{user_id}/complete")
def record_completion(user_id: str):
    feedback_mgr = get_feedback_manager()
    feedback_mgr.record_completion()
    return {"status": "ok"}


@router.post("/{user_id}/collect")
def record_collection(user_id: str):
    feedback_mgr = get_feedback_manager()
    feedback_mgr.record_collection()
    return {"status": "ok"}
