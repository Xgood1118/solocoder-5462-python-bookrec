from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.user import UserProfile, Gender, BorrowRecord
from app.storage.memory_store import get_storage

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    user_id: str
    username: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = None


class InterestTagsRequest(BaseModel):
    tags: List[str]


class BorrowRequest(BaseModel):
    book_id: str
    borrow_time: Optional[datetime] = None
    return_time: Optional[datetime] = None
    read_completion: float = Field(default=0.0, ge=0.0, le=1.0)
    read_duration: int = Field(default=0, ge=0)
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    comment: Optional[str] = None
    borrow_count: int = Field(default=1, ge=1)


@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: str):
    storage = get_storage()
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_user(req: UserCreateRequest):
    storage = get_storage()
    if storage.get_user(req.user_id):
        raise HTTPException(status_code=400, detail="User already exists")
    user = UserProfile(
        user_id=req.user_id,
        username=req.username,
        age=req.age,
        gender=req.gender,
        occupation=req.occupation,
    )
    storage.add_user(user)
    return user


@router.post("/{user_id}/interest-tags", response_model=UserProfile)
def set_interest_tags(user_id: str, req: InterestTagsRequest):
    storage = get_storage()
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.interest_tags = req.tags
    user.is_new_user = False
    return user


@router.post("/{user_id}/borrow", response_model=UserProfile)
def borrow_book(user_id: str, req: BorrowRequest):
    try:
        storage = get_storage()
        user = storage.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        book = storage.get_book(req.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        record = BorrowRecord(
            book_id=req.book_id,
            borrow_time=req.borrow_time or datetime.now(),
            return_time=req.return_time,
            read_completion=req.read_completion,
            read_duration=req.read_duration,
            rating=req.rating,
            comment=req.comment,
            borrow_count=req.borrow_count,
        )
        storage.add_borrow_record(user_id, record)

        if req.rating is not None:
            if book.avg_rating is None:
                book.avg_rating = req.rating
                book.rating_count = 1
            else:
                total = book.avg_rating * book.rating_count + req.rating
                book.rating_count += 1
                book.avg_rating = total / book.rating_count
        book.borrow_count += 1
        book.is_new_book = False

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Borrow error: {str(e)}")


@router.get("/{user_id}/borrow-history", response_model=List[BorrowRecord])
def get_borrow_history(user_id: str):
    storage = get_storage()
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.borrow_history


@router.get("", response_model=List[UserProfile])
def list_users(limit: int = 50):
    storage = get_storage()
    users = storage.get_all_users()
    return users[:limit]
