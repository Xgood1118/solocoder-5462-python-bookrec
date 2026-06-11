from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class BookFeature(BaseModel):
    book_id: str
    title: str
    author: str
    publisher: str
    publish_year: Optional[int] = None
    category: str
    tags: List[str] = Field(default_factory=list)
    word_count: int = Field(default=0, ge=0)
    cover_color: str = "unknown"
    avg_rating: Optional[float] = None
    borrow_count: int = 0
    rating_count: int = 0
    is_new_book: bool = True
    description: Optional[str] = None

    def to_feature_dict(self) -> Dict:
        return {
            "category": self.category,
            "author": self.author,
            "publisher": self.publisher,
            "publish_year": self.publish_year,
            "avg_rating": self.avg_rating,
            "borrow_count": self.borrow_count,
            "tags": self.tags,
            "word_count": self.word_count,
            "cover_color": self.cover_color,
        }
