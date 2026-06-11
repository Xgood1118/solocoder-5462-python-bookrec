from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class CollectionType(str, Enum):
    wish = "wish"
    read = "read"


class FeedbackType(str, Enum):
    like = "like"
    dislike = "dislike"
    already_read = "already_read"


class BorrowRecord(BaseModel):
    book_id: str
    borrow_time: datetime
    return_time: Optional[datetime] = None
    read_completion: float = Field(default=0.0, ge=0.0, le=1.0)
    read_duration: int = Field(default=0, ge=0)
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    comment: Optional[str] = None
    borrow_count: int = Field(default=1, ge=1)


class UserProfile(BaseModel):
    user_id: str
    username: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = None
    register_time: datetime = Field(default_factory=datetime.now)
    borrow_history: List[BorrowRecord] = Field(default_factory=list)
    collections: Dict[str, CollectionType] = Field(default_factory=dict)
    interest_tags: List[str] = Field(default_factory=list)
    is_new_user: bool = True
    avg_rating: Optional[float] = None
    total_borrow_count: int = 0
    active_hours: List[int] = Field(default_factory=list)

    def to_user_feature(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "gender": self.gender.value if self.gender else None,
            "occupation": self.occupation,
            "total_borrow_count": self.total_borrow_count,
            "avg_rating": self.avg_rating,
            "active_hours": self.active_hours,
            "interest_tags": self.interest_tags,
        }
