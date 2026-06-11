from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    like = "like"
    dislike = "dislike"
    already_read = "already_read"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            mapping = {
                "喜欢": "like",
                "不感兴趣": "dislike",
                "已读过": "already_read",
            }
            if value in mapping:
                return cls(mapping[value])
        return None


class UserFeedback(BaseModel):
    user_id: str
    book_id: str
    feedback_type: FeedbackType
    timestamp: datetime = Field(default_factory=datetime.now)
    rec_source: Optional[str] = None


class FeedbackAggregate(BaseModel):
    like_count: int = 0
    dislike_count: int = 0
    already_read_count: int = 0
