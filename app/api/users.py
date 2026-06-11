from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

from app.models.user import UserProfile, Gender, BorrowRecord
from app.storage.memory_store import get_storage

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    user_id: str
    username: str
    age: int | None = None
    gender: Gender | None = None
    occupation: str | None = None


class InterestTagsRequest(BaseModel):
    tags: List[str]


class BorrowRequest(BaseModel):
    book_id: str
    read_completion: float = 0.0
    read_duration: int = 0
    rating: float | None = None
    comment: str | None = None


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
    storage = get_storage()
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    book = storage.get_book(req.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    record = BorrowRecord(
        book_id=req.book_id,
        read_completion=req.read_completion,
        read_duration=req.read_duration,
        rating=req.rating,
        comment=req.comment,
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
