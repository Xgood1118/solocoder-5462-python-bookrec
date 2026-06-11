import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

from app.models.user import UserProfile
from app.models.book import BookFeature
from app.models.rec import RecommendItem, RecSource
from app.storage.memory_store import get_storage
from app.config import get_settings
from app.rec.collaborative import get_collaborative_filtering
from app.rec.content_based import get_content_recommender
from app.rec.knowledge_graph import get_graph_recommender
from app.feature.engineer import get_user_tags


class HybridRecommender:
    def __init__(self):
        self.settings = get_settings()
        self.storage = get_storage()
        self.cf = get_collaborative_filtering()
        self.content = get_content_recommender()
        self.graph = get_graph_recommender()

    def refresh_all(self):
        self.cf.refresh()
        self.content.refresh()
        self.graph.refresh()

    def _normalize_scores(self, scores: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        if not scores:
            return []
        max_score = max(s for _, s in scores)
        min_score = min(s for _, s in scores)
        if max_score == min_score:
            return [(bid, 0.5) for bid, _ in scores]
        return [(bid, (s - min_score) / (max_score - min_score)) for bid, s in scores]

    def _get_hybrid_scores(self, user_id: str, top_n: int = 100) -> List[Tuple[str, float]]:
        cf_scores = dict(self._normalize_scores(self.cf.recommend(user_id, top_n=top_n)))
        content_scores = dict(self._normalize_scores(self.content.recommend(user_id, top_n=top_n)))
        graph_scores = dict(self._normalize_scores(self.graph.recommend(user_id, top_n=top_n)))

        all_books = set(cf_scores.keys()) | set(content_scores.keys()) | set(graph_scores.keys())

        hybrid_scores = {}
        for book_id in all_books:
            score = 0.0
            score += self.settings.collab_weight * cf_scores.get(book_id, 0.0)
            score += self.settings.content_weight * content_scores.get(book_id, 0.0)
            score += self.settings.graph_weight * graph_scores.get(book_id, 0.0)
            hybrid_scores[book_id] = score

        sorted_scores = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n]

    def _apply_diversity(self, items: List[RecommendItem], window: int = 3) -> List[RecommendItem]:
        if len(items) < window:
            return items

        result: List[RecommendItem] = []
        remaining = list(items)
        allow_two_consecutive = False

        while remaining and len(result) < len(items):
            found = False
            for i, item in enumerate(remaining):
                book = self.storage.get_book(item.book_id)
                if not book:
                    continue

                category = book.category

                if not allow_two_consecutive and len(result) >= window - 1:
                    last_categories = [
                        self.storage.get_book(r.book_id).category
                        for r in result[-(window - 1):]
                        if self.storage.get_book(r.book_id)
                    ]
                    if len(last_categories) == window - 1 and all(c == category for c in last_categories):
                        continue

                if allow_two_consecutive and len(result) >= 2:
                    last_categories = [
                        self.storage.get_book(r.book_id).category
                        for r in result[-2:]
                        if self.storage.get_book(r.book_id)
                    ]
                    if len(last_categories) == 2 and all(c == category for c in last_categories):
                        if i < len(remaining) - 1:
                            continue

                result.append(item)
                remaining.pop(i)
                found = True
                break

            if not found:
                if not allow_two_consecutive:
                    allow_two_consecutive = True
                else:
                    if remaining:
                        result.extend(remaining)
                    break

        return result

    def _add_serendipity(self, user_id: str, items: List[RecommendItem], ratio: float = 0.1) -> List[RecommendItem]:
        user = self.storage.get_user(user_id)
        if not user:
            return items

        user_tags = set(get_user_tags(user).keys())
        user_tags.update(user.interest_tags)

        if not user_tags:
            return items

        all_books = self.storage.get_all_books()
        serendipity_candidates = []

        for book in all_books:
            book_tags = set(book.tags)
            if not book_tags:
                continue
            overlap = user_tags & book_tags
            if not overlap:
                content_scores = dict(self.content.recommend_similar_books(
                    book.book_id, top_n=1
                )) if hasattr(self.content, 'recommend_similar_books') else {}
                score = 0.3
                if book.avg_rating:
                    score += 0.3 * (book.avg_rating / 5.0)
                if book.borrow_count > 0:
                    import math
                    score += 0.2 * min(1.0, math.log10(book.borrow_count + 1) / 3.0)
                serendipity_candidates.append((book.book_id, score))

        if not serendipity_candidates:
            return items

        serendipity_candidates.sort(key=lambda x: x[1], reverse=True)

        target_count = max(1, int(len(items) * ratio))

        read_book_ids = {r.book_id for r in user.borrow_history}

        serendipity_items = []
        for book_id, score in serendipity_candidates:
            if book_id in read_book_ids:
                continue
            if any(item.book_id == book_id for item in items):
                continue
            serendipity_items.append(RecommendItem(
                book_id=book_id,
                score=score,
                source=RecSource.serendipity,
                reason="发现新大陆，探索新领域"
            ))
            if len(serendipity_items) >= target_count:
                break

        if not serendipity_items:
            return items

        result = list(items)
        step = max(1, len(result) // len(serendipity_items))
        insert_positions = [min(i * step + step // 2, len(result) - 1) for i in range(len(serendipity_items))]

        for pos, item in zip(reversed(insert_positions), reversed(serendipity_items)):
            if pos < len(result):
                result.insert(pos, item)
            else:
                result.append(item)

        return result

    def _cold_start_recommend(self, user_id: str, top_n: int = 20) -> List[RecommendItem]:
        user = self.storage.get_user(user_id)
        if not user:
            hot_books = self.storage.get_hot_books(top_n)
            return [
                RecommendItem(book_id=b.book_id, score=1.0 - i * 0.01, source=RecSource.hot, reason="热门推荐")
                for i, b in enumerate(hot_books[:top_n])
            ]

        if user.interest_tags:
            tag_recs = self.content.recommend_by_tags(user.interest_tags, top_n=top_n * 2)
            items = []
            for book_id, score in tag_recs:
                items.append(RecommendItem(
                    book_id=book_id,
                    score=score,
                    source=RecSource.cold_start,
                    reason="基于您的兴趣标签推荐"
                ))
            if not items:
                hot_books = self.storage.get_hot_books(top_n)
                items = [
                    RecommendItem(book_id=b.book_id, score=0.5, source=RecSource.hot, reason="热门推荐")
                    for b in hot_books[:top_n]
                ]
            return items[:top_n]

        hot_books = self.storage.get_hot_books(top_n)
        return [
            RecommendItem(book_id=b.book_id, score=1.0 - i * 0.01, source=RecSource.hot, reason="热门推荐")
            for i, b in enumerate(hot_books[:top_n])
        ]

    def _new_book_recommend(self, book_id: str, top_n: int = 20) -> List[RecommendItem]:
        similar = self.content.recommend_similar_books(book_id, top_n=top_n)
        items = []
        for bid, score in similar:
            items.append(RecommendItem(
                book_id=bid,
                score=score,
                source=RecSource.content,
                reason="与新书内容相似"
            ))
        return items

    def recommend(self, user_id: str, top_n: int = 20) -> Tuple[List[RecommendItem], str]:
        user = self.storage.get_user(user_id)

        if not user:
            items = self._cold_start_recommend(user_id, top_n)
            return items, "user_not_found_hot"

        if user.is_new_user or len(user.borrow_history) == 0:
            items = self._cold_start_recommend(user_id, top_n)
            return items, "cold_start"

        if self.cf.is_invalid_user(user_id):
            hot_books = self.storage.get_hot_books(top_n)
            items = [
                RecommendItem(book_id=b.book_id, score=1.0 - i * 0.01, source=RecSource.hot, reason="热门推荐")
                for i, b in enumerate(hot_books[:top_n])
            ]
            return items, "invalid_user_hot"

        hybrid_scores = self._get_hybrid_scores(user_id, top_n=top_n * 5)

        items = []
        read_book_ids = {r.book_id for r in user.borrow_history}

        for book_id, score in hybrid_scores:
            if book_id in read_book_ids:
                continue
            items.append(RecommendItem(
                book_id=book_id,
                score=score,
                source=RecSource.hybrid,
                reason="混合推荐"
            ))
            if len(items) >= top_n * 3:
                break

        items = self._apply_diversity(items, window=self.settings.diversity_window)

        items = self._add_serendipity(user_id, items, ratio=self.settings.serendipity_ratio)

        items = items[:top_n]

        return items, "hybrid"

    def recommend_for_new_book(self, book_id: str, top_n: int = 20) -> List[RecommendItem]:
        return self._new_book_recommend(book_id, top_n)

    def get_hot_books(self, top_n: int = 50) -> List[RecommendItem]:
        hot_books = self.storage.get_hot_books(top_n)
        return [
            RecommendItem(book_id=b.book_id, score=1.0 - i * 0.01, source=RecSource.hot, reason="热门榜单")
            for i, b in enumerate(hot_books)
        ]

    def calculate_diversity_index(self, items: List[RecommendItem]) -> float:
        categories = []
        for item in items:
            book = self.storage.get_book(item.book_id)
            if book and book.category:
                categories.append(book.category)
        if not categories:
            return 0.0
        unique_cats = len(set(categories))
        return unique_cats / len(categories)


_hybrid_instance = None


def get_hybrid_recommender() -> HybridRecommender:
    global _hybrid_instance
    if _hybrid_instance is None:
        _hybrid_instance = HybridRecommender()
    return _hybrid_instance
