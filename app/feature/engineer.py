import math
import re
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

from app.models.user import UserProfile, BorrowRecord
from app.models.book import BookFeature


STOP_WORDS = {
    "的", "了", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "那", "他", "她",
    "它", "们", "这个", "那个", "什么", "怎么", "为什么", "可以",
    "但是", "因为", "所以", "如果", "虽然", "还是", "已经", "正在",
    "书", "本", "本儿", "部", "小说", "故事", "内容", "情节",
    "不错", "好看", "喜欢", "推荐", "觉得", "感觉", "真的", "非常",
}


def extract_keywords(text: str, top_k: int = 5) -> List[str]:
    if not text:
        return []
    if HAS_JIEBA:
        words = jieba.lcut(text)
    else:
        words = re.findall(r"[\w\u4e00-\u9fff]+", text)
    filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_k)]


def calculate_borrow_weight(borrow_count: int) -> float:
    if borrow_count <= 0:
        return 0.0
    if borrow_count == 1:
        return 1.0
    if borrow_count == 2:
        return 1.5
    if borrow_count == 3:
        return 1.8
    return 1.0 + 0.8 * (1 - math.exp(-(borrow_count - 1) * 0.3))


def compute_interaction_score(record: BorrowRecord, user_avg_rating: Optional[float] = None) -> float:
    score = 0.0
    borrow_weight = calculate_borrow_weight(record.borrow_count)
    score += 0.3 * borrow_weight
    score += 0.3 * record.read_completion
    if record.read_duration > 0:
        normalized_duration = min(1.0, record.read_duration / 3600.0)
        score += 0.15 * normalized_duration
    if record.rating is not None:
        if user_avg_rating is not None:
            adjusted_rating = (record.rating - user_avg_rating) / 2.0 + 0.5
            adjusted_rating = max(0.0, min(1.0, adjusted_rating))
            score += 0.25 * adjusted_rating
        else:
            score += 0.25 * (record.rating / 5.0)
    if record.comment:
        score += 0.05
    return min(1.0, score)


def get_user_tags(user: UserProfile) -> Counter:
    tag_counter = Counter()
    for record in user.borrow_history:
        book = None
        from app.storage.memory_store import get_storage
        storage = get_storage()
        book = storage.get_book(record.book_id)
        if not book:
            continue
        weight = compute_interaction_score(record, user.avg_rating)
        for tag in book.tags:
            tag_counter[tag] += weight
        if book.category:
            tag_counter[book.category] += weight * 1.5
    return tag_counter


def build_user_feature_vector(user: UserProfile) -> Dict:
    tag_counter = get_user_tags(user)
    top_tags = [tag for tag, _ in tag_counter.most_common(20)]
    feature = {
        "age": user.age,
        "gender": user.gender.value if user.gender else None,
        "occupation": user.occupation,
        "total_borrow_count": user.total_borrow_count,
        "avg_rating": user.avg_rating,
        "active_hours": user.active_hours,
        "top_tags": top_tags,
        "tag_weights": dict(tag_counter),
        "interest_tags": user.interest_tags,
    }
    return feature


def build_book_feature_vector(book: BookFeature) -> Dict:
    feature = {
        "category": book.category,
        "author": book.author,
        "publisher": book.publisher,
        "publish_year": book.publish_year,
        "avg_rating": book.avg_rating,
        "borrow_count": book.borrow_count,
        "tags": set(book.tags),
        "word_count": book.word_count,
        "cover_color": book.cover_color,
    }
    return feature


def extract_book_keywords(book: BookFeature) -> List[str]:
    keywords = []
    if book.description:
        keywords = extract_keywords(book.description, top_k=5)
    keywords.extend(book.tags)
    return list(set(keywords))
