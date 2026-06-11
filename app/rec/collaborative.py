import math
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from app.models.user import UserProfile, BorrowRecord
from app.storage.memory_store import get_storage
from app.config import get_settings
from app.feature.engineer import compute_interaction_score


class CollaborativeFiltering:
    def __init__(self):
        self.settings = get_settings()
        self.storage = get_storage()
        self.user_avg_ratings: Dict[str, float] = {}
        self.user_book_ratings: Dict[str, Dict[str, float]] = {}
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        self._build_rating_matrix()

    def _build_rating_matrix(self):
        users = self.storage.get_all_users()
        for user in users:
            self.user_avg_ratings[user.user_id] = user.avg_rating or 3.0
            book_scores = {}
            for record in user.borrow_history:
                score = compute_interaction_score(record, user.avg_rating)
                book_scores[record.book_id] = score
            self.user_book_ratings[user.user_id] = book_scores

    def refresh(self):
        self.user_avg_ratings.clear()
        self.user_book_ratings.clear()
        self.similarity_cache.clear()
        self._build_rating_matrix()

    def adjusted_cosine_similarity(self, user_id1: str, user_id2: str) -> float:
        cache_key = tuple(sorted([user_id1, user_id2]))
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        ratings1 = self.user_book_ratings.get(user_id1, {})
        ratings2 = self.user_book_ratings.get(user_id2, {})

        common_books = set(ratings1.keys()) & set(ratings2.keys())
        if len(common_books) < 2:
            self.similarity_cache[cache_key] = 0.0
            return 0.0

        avg1 = self.user_avg_ratings.get(user_id1, 3.0)
        avg2 = self.user_avg_ratings.get(user_id2, 3.0)

        numerator = 0.0
        denom1 = 0.0
        denom2 = 0.0

        for book_id in common_books:
            r1 = ratings1[book_id] - avg1 / 5.0
            r2 = ratings2[book_id] - avg2 / 5.0
            numerator += r1 * r2
            denom1 += r1 * r1
            denom2 += r2 * r2

        if denom1 == 0 or denom2 == 0:
            self.similarity_cache[cache_key] = 0.0
            return 0.0

        similarity = numerator / (math.sqrt(denom1) * math.sqrt(denom2))
        similarity = max(-1.0, min(1.0, similarity))
        similarity = (similarity + 1.0) / 2.0

        self.similarity_cache[cache_key] = similarity
        return similarity

    def find_similar_users(self, user_id: str, k: int = 20) -> List[Tuple[str, float]]:
        target_user = self.storage.get_user(user_id)
        if not target_user:
            return []

        all_users = self.storage.get_all_users()
        similarities = []

        for other_user in all_users:
            if other_user.user_id == user_id:
                continue
            if len(other_user.borrow_history) < 3:
                continue
            sim = self.adjusted_cosine_similarity(user_id, other_user.user_id)
            if sim > self.settings.similarity_threshold:
                similarities.append((other_user.user_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

    def is_invalid_user(self, user_id: str) -> bool:
        similar_users = self.find_similar_users(user_id, k=5)
        if not similar_users:
            return True
        avg_sim = sum(sim for _, sim in similar_users) / len(similar_users)
        return avg_sim < self.settings.similarity_threshold

    def recommend(self, user_id: str, top_n: int = 50) -> List[Tuple[str, float]]:
        target_user = self.storage.get_user(user_id)
        if not target_user:
            return []

        if len(target_user.borrow_history) == 0:
            return []

        similar_users = self.find_similar_users(user_id, k=self.settings.collab_k)
        if not similar_users:
            return []

        user_books = set(self.user_book_ratings.get(user_id, {}).keys())
        book_scores: Dict[str, float] = defaultdict(float)
        similarity_sums: Dict[str, float] = defaultdict(float)

        for sim_user_id, similarity in similar_users:
            sim_ratings = self.user_book_ratings.get(sim_user_id, {})
            for book_id, rating in sim_ratings.items():
                if book_id in user_books:
                    continue
                book_scores[book_id] += similarity * rating
                similarity_sums[book_id] += similarity

        normalized_scores = []
        for book_id, total_score in book_scores.items():
            if similarity_sums[book_id] > 0:
                normalized = total_score / similarity_sums[book_id]
                normalized_scores.append((book_id, normalized))

        normalized_scores.sort(key=lambda x: x[1], reverse=True)
        return normalized_scores[:top_n]


_cf_instance = None


def get_collaborative_filtering() -> CollaborativeFiltering:
    global _cf_instance
    if _cf_instance is None:
        _cf_instance = CollaborativeFiltering()
    return _cf_instance
