import json
import os
from typing import Dict, List, Optional
from pathlib import Path

from app.models.user import UserProfile, BorrowRecord
from app.models.book import BookFeature
from app.config import get_settings


class InMemoryStorage:
    def __init__(self):
        self.settings = get_settings()
        self.users: Dict[str, UserProfile] = {}
        self.books: Dict[str, BookFeature] = {}
        self._load_from_seed()

    def _load_from_seed(self):
        data_dir = Path(self.settings.data_dir)
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            return

        users_file = data_dir / "users.json"
        books_file = data_dir / "books.json"

        if users_file.exists():
            with open(users_file, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                for user_data in users_data:
                    user = UserProfile(**user_data)
                    self.users[user.user_id] = user

        if books_file.exists():
            with open(books_file, "r", encoding="utf-8") as f:
                books_data = json.load(f)
                for book_data in books_data:
                    book = BookFeature(**book_data)
                    self.books[book.book_id] = book

    def save_to_seed(self):
        data_dir = Path(self.settings.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        users_data = [user.model_dump(mode="json") for user in self.users.values()]
        with open(data_dir / "users.json", "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)

        books_data = [book.model_dump(mode="json") for book in self.books.values()]
        with open(data_dir / "books.json", "w", encoding="utf-8") as f:
            json.dump(books_data, f, ensure_ascii=False, indent=2)

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        return self.users.get(user_id)

    def add_user(self, user: UserProfile):
        self.users[user.user_id] = user

    def update_user(self, user_id: str, **kwargs):
        if user_id in self.users:
            for key, value in kwargs.items():
                if hasattr(self.users[user_id], key):
                    setattr(self.users[user_id], key, value)

    def get_book(self, book_id: str) -> Optional[BookFeature]:
        return self.books.get(book_id)

    def add_book(self, book: BookFeature):
        self.books[book.book_id] = book

    def add_borrow_record(self, user_id: str, record: BorrowRecord):
        user = self.users.get(user_id)
        if not user:
            return
        existing = None
        for r in user.borrow_history:
            if r.book_id == record.book_id:
                existing = r
                break
        if existing:
            existing.borrow_count += 1
            existing.read_duration += record.read_duration
            if record.read_completion > existing.read_completion:
                existing.read_completion = record.read_completion
            if record.rating is not None:
                existing.rating = record.rating
            if record.comment:
                existing.comment = record.comment
        else:
            user.borrow_history.append(record)
            user.total_borrow_count += 1
        user.is_new_user = False
        self._update_user_stats(user_id)

    def _update_user_stats(self, user_id: str):
        user = self.users.get(user_id)
        if not user:
            return
        ratings = [r.rating for r in user.borrow_history if r.rating is not None]
        if ratings:
            user.avg_rating = sum(ratings) / len(ratings)

    def get_hot_books(self, top_n: int = 50) -> List[BookFeature]:
        sorted_books = sorted(
            self.books.values(),
            key=lambda b: (b.borrow_count, b.avg_rating or 0),
            reverse=True
        )
        return sorted_books[:top_n]

    def get_all_users(self) -> List[UserProfile]:
        return list(self.users.values())

    def get_all_books(self) -> List[BookFeature]:
        return list(self.books.values())


_storage_instance = None


def get_storage() -> InMemoryStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = InMemoryStorage()
    return _storage_instance
