from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from app.models.feedback import UserFeedback, FeedbackType, FeedbackAggregate
from app.models.user import UserProfile
from app.storage.memory_store import get_storage


class FeedbackManager:
    def __init__(self):
        self.storage = get_storage()
        self.user_feedbacks: Dict[str, List[UserFeedback]] = defaultdict(list)
        self.disliked_tags: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.already_read_books: Dict[str, set] = defaultdict(set)
        self.weekly_impressions: int = 0
        self.weekly_clicks: int = 0
        self.weekly_completions: int = 0
        self.weekly_collections: int = 0
        self.week_start: datetime = self._get_week_start()

    def _get_week_start(self) -> datetime:
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)

    def _check_week_reset(self):
        current_week = self._get_week_start()
        if current_week > self.week_start:
            self.week_start = current_week
            self.weekly_impressions = 0
            self.weekly_clicks = 0
            self.weekly_completions = 0
            self.weekly_collections = 0

    def add_feedback(self, feedback: UserFeedback):
        self._check_week_reset()
        self.user_feedbacks[feedback.user_id].append(feedback)

        book = self.storage.get_book(feedback.book_id)
        if not book:
            return

        if feedback.feedback_type == FeedbackType.dislike:
            for tag in book.tags:
                self.disliked_tags[feedback.user_id][tag] += 0.1
            if book.category:
                self.disliked_tags[feedback.user_id][book.category] += 0.2

        elif feedback.feedback_type == FeedbackType.already_read:
            self.already_read_books[feedback.user_id].add(feedback.book_id)

        elif feedback.feedback_type == FeedbackType.like:
            self.weekly_clicks += 1

    def record_impression(self, count: int = 1):
        self._check_week_reset()
        self.weekly_impressions += count

    def record_click(self, count: int = 1):
        self._check_week_reset()
        self.weekly_clicks += count

    def record_completion(self, count: int = 1):
        self._check_week_reset()
        self.weekly_completions += count

    def record_collection(self, count: int = 1):
        self._check_week_reset()
        self.weekly_collections += count

    def get_dislike_penalty(self, user_id: str, book_id: str) -> float:
        book = self.storage.get_book(book_id)
        if not book:
            return 0.0

        penalty = 0.0
        user_dislikes = self.disliked_tags.get(user_id, {})

        for tag in book.tags:
            penalty += user_dislikes.get(tag, 0.0)

        if book.category:
            penalty += user_dislikes.get(book.category, 0.0)

        return min(1.0, penalty)

    def is_already_read(self, user_id: str, book_id: str) -> bool:
        return book_id in self.already_read_books.get(user_id, set())

    def apply_feedback_to_scores(
        self, user_id: str, scores: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        result = []
        for book_id, score in scores:
            if self.is_already_read(user_id, book_id):
                continue
            penalty = self.get_dislike_penalty(user_id, book_id)
            adjusted_score = score * (1.0 - penalty)
            result.append((book_id, adjusted_score))
        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def get_user_feedback_summary(self, user_id: str) -> FeedbackAggregate:
        feedbacks = self.user_feedbacks.get(user_id, [])
        agg = FeedbackAggregate()
        for fb in feedbacks:
            if fb.feedback_type == FeedbackType.like:
                agg.like_count += 1
            elif fb.feedback_type == FeedbackType.dislike:
                agg.dislike_count += 1
            elif fb.feedback_type == FeedbackType.already_read:
                agg.already_read_count += 1
        return agg

    def get_weekly_stats(self) -> Dict[str, float]:
        self._check_week_reset()
        ctr = self.weekly_clicks / self.weekly_impressions if self.weekly_impressions > 0 else 0.0
        completion_rate = self.weekly_completions / self.weekly_clicks if self.weekly_clicks > 0 else 0.0
        collection_rate = self.weekly_collections / self.weekly_clicks if self.weekly_clicks > 0 else 0.0
        return {
            "week_start": self.week_start.strftime("%Y-%m-%d"),
            "impressions": self.weekly_impressions,
            "clicks": self.weekly_clicks,
            "click_through_rate": ctr,
            "completion_rate": completion_rate,
            "collection_rate": collection_rate,
        }


_feedback_instance = None


def get_feedback_manager() -> FeedbackManager:
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = FeedbackManager()
    return _feedback_instance
