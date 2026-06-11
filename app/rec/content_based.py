import math
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from app.models.user import UserProfile
from app.models.book import BookFeature
from app.storage.memory_store import get_storage
from app.feature.engineer import compute_interaction_score, get_user_tags


COLOR_RGB_MAP = {
    "red": (255, 0, 0),
    "crimson": (220, 20, 60),
    "pink": (255, 192, 203),
    "hotpink": (255, 105, 180),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "gold": (255, 215, 0),
    "green": (0, 128, 0),
    "lime": (0, 255, 0),
    "teal": (0, 128, 128),
    "cyan": (0, 255, 255),
    "blue": (0, 0, 255),
    "navy": (0, 0, 128),
    "skyblue": (135, 206, 235),
    "darkblue": (0, 0, 139),
    "deepblue": (25, 25, 112),
    "purple": (128, 0, 128),
    "violet": (238, 130, 238),
    "indigo": (75, 0, 130),
    "brown": (139, 69, 19),
    "tan": (210, 180, 140),
    "beige": (245, 245, 220),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "silver": (192, 192, 192),
    "unknown": (128, 128, 128),
}


def color_similarity(color1: str, color2: str) -> float:
    if color1 == color2:
        return 1.0
    rgb1 = COLOR_RGB_MAP.get(color1, (128, 128, 128))
    rgb2 = COLOR_RGB_MAP.get(color2, (128, 128, 128))
    distance = math.sqrt(
        (rgb1[0] - rgb2[0]) ** 2 +
        (rgb1[1] - rgb2[1]) ** 2 +
        (rgb1[2] - rgb2[2]) ** 2
    )
    max_distance = math.sqrt(255 ** 2 * 3)
    return 1.0 - (distance / max_distance)


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 and not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def cosine_similarity_tags(tags1: Dict[str, float], tags2: Set[str]) -> float:
    if not tags1 or not tags2:
        return 0.0
    dot_product = 0.0
    for tag in tags2:
        dot_product += tags1.get(tag, 0.0)
    norm1 = math.sqrt(sum(v ** 2 for v in tags1.values()))
    norm2 = math.sqrt(len(tags2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


class ContentBasedRecommender:
    def __init__(self):
        self.storage = get_storage()
        self._tag_index: Dict[str, List[str]] = defaultdict(list)
        self._category_index: Dict[str, List[str]] = defaultdict(list)
        self._author_index: Dict[str, List[str]] = defaultdict(list)
        self._build_indexes()

    def _build_indexes(self):
        books = self.storage.get_all_books()
        for book in books:
            for tag in book.tags:
                self._tag_index[tag].append(book.book_id)
            if book.category:
                self._category_index[book.category].append(book.book_id)
            if book.author:
                self._author_index[book.author].append(book.book_id)

    def refresh(self):
        self._tag_index.clear()
        self._category_index.clear()
        self._author_index.clear()
        self._build_indexes()

    def compute_book_similarity(self, book1: BookFeature, book2: BookFeature) -> float:
        score = 0.0

        tags1 = set(book1.tags)
        tags2 = set(book2.tags)
        tag_sim = jaccard_similarity(tags1, tags2)
        score += 0.35 * tag_sim

        if book1.category and book2.category:
            score += 0.25 if book1.category == book2.category else 0.0

        if book1.author and book2.author:
            score += 0.15 if book1.author == book2.author else 0.0

        if book1.publisher and book2.publisher:
            score += 0.05 if book1.publisher == book2.publisher else 0.0

        color_sim = color_similarity(book1.cover_color, book2.cover_color)
        score += 0.1 * color_sim

        if book1.word_count > 0 and book2.word_count > 0:
            wc_ratio = min(book1.word_count, book2.word_count) / max(book1.word_count, book2.word_count)
            score += 0.05 * wc_ratio

        if book1.publish_year and book2.publish_year:
            year_diff = abs(book1.publish_year - book2.publish_year)
            year_score = max(0.0, 1.0 - year_diff / 50.0)
            score += 0.05 * year_score

        return score

    def recommend(self, user_id: str, top_n: int = 50) -> List[Tuple[str, float]]:
        user = self.storage.get_user(user_id)
        if not user:
            return []

        if not user.borrow_history and not user.interest_tags:
            return []

        user_tag_weights = dict(get_user_tags(user))
        for tag in user.interest_tags:
            user_tag_weights[tag] = user_tag_weights.get(tag, 0.0) + 0.5

        if not user_tag_weights:
            return []

        candidate_books: Set[str] = set()
        for tag in user_tag_weights:
            if tag in self._tag_index:
                candidate_books.update(self._tag_index[tag])
        if user.borrow_history:
            last_book = user.borrow_history[-1]
            book = self.storage.get_book(last_book.book_id)
            if book:
                if book.category in self._category_index:
                    candidate_books.update(self._category_index[book.category])
                if book.author in self._author_index:
                    candidate_books.update(self._author_index[book.author])

        user_book_ids = {r.book_id for r in user.borrow_history}
        candidate_books -= user_book_ids

        if not candidate_books:
            return []

        book_scores: List[Tuple[str, float]] = []
        for book_id in candidate_books:
            book = self.storage.get_book(book_id)
            if not book:
                continue

            tag_score = cosine_similarity_tags(user_tag_weights, set(book.tags))
            score = 0.6 * tag_score

            if book.avg_rating:
                score += 0.2 * (book.avg_rating / 5.0)

            if book.borrow_count > 0:
                popularity = min(1.0, math.log10(book.borrow_count + 1) / 3.0)
                score += 0.2 * popularity

            book_scores.append((book_id, score))

        book_scores.sort(key=lambda x: x[1], reverse=True)
        return book_scores[:top_n]

    def recommend_similar_books(self, book_id: str, top_n: int = 20) -> List[Tuple[str, float]]:
        target_book = self.storage.get_book(book_id)
        if not target_book:
            return []

        candidate_books: Set[str] = set()
        for tag in target_book.tags:
            if tag in self._tag_index:
                candidate_books.update(self._tag_index[tag])
        if target_book.category in self._category_index:
            candidate_books.update(self._category_index[target_book.category])

        candidate_books.discard(book_id)

        if not candidate_books:
            return []

        similarities = []
        for cand_id in candidate_books:
            cand_book = self.storage.get_book(cand_id)
            if not cand_book:
                continue
            sim = self.compute_book_similarity(target_book, cand_book)
            similarities.append((cand_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]

    def recommend_by_tags(self, tags: List[str], top_n: int = 50) -> List[Tuple[str, float]]:
        if not tags:
            return []

        tag_set = set(tags)
        candidate_books: Set[str] = set()
        for tag in tags:
            if tag in self._tag_index:
                candidate_books.update(self._tag_index[tag])

        if not candidate_books:
            return []

        scores = []
        for book_id in candidate_books:
            book = self.storage.get_book(book_id)
            if not book:
                continue
            book_tags = set(book.tags)
            sim = jaccard_similarity(tag_set, book_tags)
            scores.append((book_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]


_content_instance = None


def get_content_recommender() -> ContentBasedRecommender:
    global _content_instance
    if _content_instance is None:
        _content_instance = ContentBasedRecommender()
    return _content_instance
