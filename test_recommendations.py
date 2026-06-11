import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage.memory_store import get_storage
from app.rec.hybrid import get_hybrid_recommender
from app.rec.collaborative import get_collaborative_filtering
from app.rec.content_based import get_content_recommender
from app.rec.knowledge_graph import get_graph_recommender
from app.feedback.manager import get_feedback_manager
from app.models.feedback import FeedbackType, UserFeedback

storage = get_storage()
print(f"Users: {len(storage.users)}, Books: {len(storage.books)}")

users = storage.get_all_users()
active_users = [u for u in users if len(u.borrow_history) > 5]
print(f"Active users (5+ borrows): {len(active_users)}")

if active_users:
    test_user = active_users[0]
    print(f"\nTest user: {test_user.user_id} ({test_user.username})")
    print(f"  Borrow count: {test_user.total_borrow_count}")
    print(f"  Avg rating: {test_user.avg_rating}")
    print(f"  Is new user: {test_user.is_new_user}")

    cf = get_collaborative_filtering()
    cf_recs = cf.recommend(test_user.user_id, top_n=10)
    print(f"\nCollaborative recommendations: {len(cf_recs)}")
    for bid, score in cf_recs[:5]:
        book = storage.get_book(bid)
        print(f"  {bid} - {book.title if book else '?'} ({score:.3f})")

    content = get_content_recommender()
    content_recs = content.recommend(test_user.user_id, top_n=10)
    print(f"\nContent recommendations: {len(content_recs)}")
    for bid, score in content_recs[:5]:
        book = storage.get_book(bid)
        print(f"  {bid} - {book.title if book else '?'} ({score:.3f})")

    graph = get_graph_recommender()
    graph_recs = graph.recommend(test_user.user_id, top_n=10)
    print(f"\nGraph recommendations: {len(graph_recs)}")
    for bid, score in graph_recs[:5]:
        book = storage.get_book(bid)
        print(f"  {bid} - {book.title if book else '?'} ({score:.3f})")

    hybrid = get_hybrid_recommender()
    hybrid_recs, strategy = hybrid.recommend(test_user.user_id, top_n=10)
    print(f"\nHybrid recommendations: {len(hybrid_recs)} (strategy: {strategy})")
    for item in hybrid_recs[:5]:
        book = storage.get_book(item.book_id)
        print(f"  {item.book_id} - {book.title if book else '?'} (score={item.score:.3f}, source={item.source.value})")

    diversity = hybrid.calculate_diversity_index(hybrid_recs)
    print(f"  Diversity index: {diversity:.3f}")

new_users = [u for u in users if u.is_new_user]
print(f"\nNew users: {len(new_users)}")
if new_users:
    nu = new_users[0]
    print(f"Cold start test user: {nu.user_id} (interest_tags: {nu.interest_tags})")
    cold_recs, strategy = hybrid.recommend(nu.user_id, top_n=10)
    print(f"  Cold start recs: {len(cold_recs)} (strategy: {strategy})")
    for item in cold_recs[:3]:
        book = storage.get_book(item.book_id)
        print(f"    {item.book_id} - {book.title if book else '?'} (source={item.source.value})")

print("\n--- Feedback test ---")
fb = get_feedback_manager()
if active_users:
    test_user_id = active_users[0].user_id
    book_id = cf_recs[0][0] if cf_recs else "b0001"
    fb.add_feedback(UserFeedback(
        user_id=test_user_id,
        book_id=book_id,
        feedback_type=FeedbackType.dislike,
    ))
    print(f"Dislike feedback added for user={test_user_id}, book={book_id}")
    summary = fb.get_user_feedback_summary(test_user_id)
    print(f"  Feedback summary: like={summary.like_count}, dislike={summary.dislike_count}, already_read={summary.already_read_count}")

print("\n--- AB Test ---")
from app.abtest.manager import get_abtest_manager
ab = get_abtest_manager()
ab.start_test("v1", "v2")
print(f"AB test started: phase={ab.get_state().current_phase.value}")
print(f"  Weights: old={ab.get_state().old_model_weight}, new={ab.get_state().new_model_weight}")
ab.advance_phase()
print(f"  After advance: phase={ab.get_state().current_phase.value}")

print("\nAll tests passed!")
