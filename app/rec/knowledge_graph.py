import math
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from app.models.user import UserProfile
from app.models.book import BookFeature
from app.storage.memory_store import get_storage
from app.config import get_settings
from app.feature.engineer import get_user_tags


class KnowledgeGraphRecommender:
    def __init__(self):
        self.settings = get_settings()
        self.storage = get_storage()
        self.tag_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.tag_book_count: Dict[str, int] = defaultdict(int)
        self.total_books: int = 0
        self.pmi_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.tag_books: Dict[str, List[str]] = defaultdict(list)
        self.pagerank_scores: Dict[str, float] = {}
        self._build_graph()

    def _build_graph(self):
        books = self.storage.get_all_books()
        self.total_books = len(books)

        for book in books:
            tags = book.tags
            for tag in tags:
                self.tag_book_count[tag] += 1
                self.tag_books[tag].append(book.book_id)

            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    t1, t2 = tags[i], tags[j]
                    self.tag_cooccurrence[t1][t2] += 1
                    self.tag_cooccurrence[t2][t1] += 1

        self._compute_pmi()
        self._compute_pagerank()

    def _compute_pmi(self):
        for tag1, neighbors in self.tag_cooccurrence.items():
            for tag2, co_count in neighbors.items():
                p_tag1 = self.tag_book_count.get(tag1, 0) / self.total_books if self.total_books > 0 else 0
                p_tag2 = self.tag_book_count.get(tag2, 0) / self.total_books if self.total_books > 0 else 0
                p_both = co_count / self.total_books if self.total_books > 0 else 0

                if p_tag1 == 0 or p_tag2 == 0 or p_both == 0:
                    pmi = 0.0
                else:
                    pmi = math.log(p_both / (p_tag1 * p_tag2))

                self.pmi_matrix[tag1][tag2] = pmi

    def _compute_pagerank(self, damping: float = 0.85, max_iter: int = 50, tol: float = 1e-6):
        valid_tags = set()
        for tag1, neighbors in self.pmi_matrix.items():
            for tag2, pmi in neighbors.items():
                if pmi > self.settings.pmi_threshold:
                    valid_tags.add(tag1)
                    valid_tags.add(tag2)

        if not valid_tags:
            return

        n = len(valid_tags)
        tag_list = list(valid_tags)
        tag_idx = {tag: i for i, tag in enumerate(tag_list)}

        adjacency = [[] for _ in range(n)]
        for i, tag in enumerate(tag_list):
            neighbors = self.pmi_matrix.get(tag, {})
            for n_tag, pmi in neighbors.items():
                if pmi > self.settings.pmi_threshold and n_tag in tag_idx:
                    j = tag_idx[n_tag]
                    adjacency[i].append((j, pmi))

        scores = [1.0 / n] * n

        for _ in range(max_iter):
            new_scores = [(1 - damping) / n] * n
            for i in range(n):
                if not adjacency[i]:
                    continue
                total_weight = sum(w for _, w in adjacency[i])
                if total_weight == 0:
                    continue
                for j, weight in adjacency[i]:
                    new_scores[j] += damping * scores[i] * (weight / total_weight)

            diff = sum(abs(new_scores[i] - scores[i]) for i in range(n))
            scores = new_scores

            if diff < tol:
                break

        for i, tag in enumerate(tag_list):
            self.pagerank_scores[tag] = scores[i]

    def refresh(self):
        self.tag_cooccurrence.clear()
        self.tag_book_count.clear()
        self.tag_books.clear()
        self.pmi_matrix.clear()
        self.pagerank_scores.clear()
        self.total_books = 0
        self._build_graph()

    def get_related_tags(self, tag: str, top_n: int = 10) -> List[Tuple[str, float]]:
        if tag not in self.pmi_matrix:
            return []
        neighbors = [
            (t, pmi) for t, pmi in self.pmi_matrix[tag].items()
            if pmi > self.settings.pmi_threshold
        ]
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors[:top_n]

    def recommend(self, user_id: str, top_n: int = 50) -> List[Tuple[str, float]]:
        user = self.storage.get_user(user_id)
        if not user:
            return []

        user_tag_counter = get_user_tags(user)
        if not user_tag_counter:
            return []

        user_tags = set(user_tag_counter.keys())
        user_book_ids = {r.book_id for r in user.borrow_history}

        expanded_tags: Dict[str, float] = {}
        for tag, weight in user_tag_counter.items():
            expanded_tags[tag] = weight
            related = self.get_related_tags(tag, top_n=5)
            for rel_tag, pmi in related:
                normalized_pmi = max(0.0, min(1.0, pmi / 3.0))
                expanded_tags[rel_tag] = expanded_tags.get(rel_tag, 0.0) + weight * normalized_pmi * 0.5

        tag_pr_scores = {}
        for tag in expanded_tags:
            pr = self.pagerank_scores.get(tag, 0.0)
            tag_pr_scores[tag] = expanded_tags[tag] * (1 + pr)

        candidate_books: Dict[str, float] = defaultdict(float)
        for tag, weight in tag_pr_scores.items():
            books_for_tag = self.tag_books.get(tag, [])
            for book_id in books_for_tag:
                if book_id in user_book_ids:
                    continue
                candidate_books[book_id] += weight

        if not candidate_books:
            return []

        max_score = max(candidate_books.values()) if candidate_books else 1.0
        if max_score > 0:
            normalized = {
                book_id: score / max_score
                for book_id, score in candidate_books.items()
            }
        else:
            normalized = candidate_books

        sorted_books = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        return sorted_books[:top_n]

    def get_tag_pagerank(self, tag: str) -> float:
        return self.pagerank_scores.get(tag, 0.0)


_graph_instance = None


def get_graph_recommender() -> KnowledgeGraphRecommender:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = KnowledgeGraphRecommender()
    return _graph_instance
