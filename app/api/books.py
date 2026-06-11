from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

from app.models.book import BookFeature
from app.storage.memory_store import get_storage
from app.rec.content_based import get_content_recommender

router = APIRouter(prefix="/books", tags=["books"])


class BookCreateRequest(BaseModel):
    book_id: str
    title: str
    author: str
    publisher: str
    publish_year: int | None = None
    category: str
    tags: List[str] = []
    word_count: int = 0
    cover_color: str = "unknown"
    description: str | None = None


@router.get("/{book_id}", response_model=BookFeature)
def get_book(book_id: str):
    storage = get_storage()
    book = storage.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("", response_model=BookFeature, status_code=status.HTTP_201_CREATED)
def create_book(req: BookCreateRequest):
    storage = get_storage()
    if storage.get_book(req.book_id):
        raise HTTPException(status_code=400, detail="Book already exists")
    book = BookFeature(
        book_id=req.book_id,
        title=req.title,
        author=req.author,
        publisher=req.publisher,
        publish_year=req.publish_year,
        category=req.category,
        tags=req.tags,
        word_count=req.word_count,
        cover_color=req.cover_color,
        description=req.description,
    )
    storage.add_book(book)
    return book


@router.get("", response_model=List[BookFeature])
def list_books(limit: int = 50, category: str | None = None):
    storage = get_storage()
    books = storage.get_all_books()
    if category:
        books = [b for b in books if b.category == category]
    return books[:limit]


@router.get("/{book_id}/similar", response_model=List[str])
def get_similar_books(book_id: str, top_n: int = 20):
    content_rec = get_content_recommender()
    similar = content_rec.recommend_similar_books(book_id, top_n=top_n)
    return [book_id for book_id, _ in similar]


@router.get("/hot/list", response_model=List[BookFeature])
def get_hot_books(top_n: int = 50):
    storage = get_storage()
    return storage.get_hot_books(top_n)
