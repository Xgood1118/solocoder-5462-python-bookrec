import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage.memory_store import get_storage
from app.rec.hybrid import HybridRecommender, get_hybrid_recommender
from app.rec.collaborative import get_collaborative_filtering
from app.models.rec import RecommendItem, RecSource

storage = get_storage()

def check_no_3_consecutive(items, label):
    cats = []
    for item in items:
        book = storage.get_book(item.book_id)
        cats.append(book.category if book else "?")
    
    violations = []
    for i in range(len(cats) - 2):
        if cats[i] == cats[i+1] == cats[i+2]:
            violations.append((i, cats[i]))
    
    if violations:
        print(f"  FAIL [{label}]: {len(violations)} violations of 3-consecutive rule")
        for pos, cat in violations:
            print(f"    positions {pos}-{pos+2}: all '{cat}'")
        print(f"    full category sequence: {' -> '.join(cats)}")
        return False
    else:
        print(f"  PASS [{label}]: no 3-consecutive violations in {len(items)} items")
        return True

print("=== Test 1: Hybrid recommendation diversity ===")
rec = HybridRecommender()

users = storage.get_all_users()
active_users = [u for u in users if len(u.borrow_history) > 5]
if active_users:
    test_user = active_users[0]
    items, strategy = rec.recommend(test_user.user_id, top_n=20)
    print(f"  user={test_user.user_id}, strategy={strategy}, items={len(items)}")
    check_no_3_consecutive(items, f"hybrid/{test_user.user_id}")

print("\n=== Test 2: Multiple users diversity check ===")
all_pass = True
for u in active_users[:10]:
    items, strategy = rec.recommend(u.user_id, top_n=20)
    passed = check_no_3_consecutive(items, f"{strategy}/{u.user_id}")
    all_pass = all_pass and passed

print(f"\n  Overall diversity: {'ALL PASS' if all_pass else 'SOME FAILED'}")

print("\n=== Test 3: Invalid user hot fallback diversity ===")
cf = get_collaborative_filtering()
for u in users:
    if len(u.borrow_history) > 0 and cf.is_invalid_user(u.user_id):
        items, strategy = rec.recommend(u.user_id, top_n=20)
        print(f"  Invalid user: {u.user_id}, strategy={strategy}")
        check_no_3_consecutive(items, f"invalid_hot/{u.user_id}")
        break
else:
    print("  No invalid users in sample data, creating one...")
    from app.models.user import UserProfile, BorrowRecord
    fake_user = UserProfile(user_id="fake_invalid", username="fake", is_new_user=False)
    for _ in range(5):
        fake_user.borrow_history.append(BorrowRecord(book_id="b0001", rating=5.0, read_completion=1.0))
    fake_user.avg_rating = 5.0
    storage.add_user(fake_user)
    items, strategy = rec.recommend("fake_invalid", top_n=20)
    print(f"  Fake invalid user: strategy={strategy}")
    check_no_3_consecutive(items, f"fake_invalid/{strategy}")

print("\n=== Test 4: Cold start with interest tags ===")
from app.models.user import UserProfile
cold_user = UserProfile(user_id="cold_tag_user", username="cold_tag", is_new_user=True, interest_tags=["科幻", "太空", "人工智能"])
storage.add_user(cold_user)

items, strategy = rec.recommend("cold_tag_user", top_n=20)
print(f"  Cold user with tags: strategy={strategy}, items={len(items)}")
cold_sources = set(item.source.value for item in items)
print(f"  Sources used: {cold_sources}")
has_cold_start = "cold_start" in cold_sources
print(f"  Interest tag matching: {'PASS' if has_cold_start else 'FAIL'}")

if items:
    for item in items[:5]:
        book = storage.get_book(item.book_id)
        if book:
            print(f"    {item.book_id} - {book.title} ({book.category}) [source={item.source.value}]")

print("\n=== Test 5: Cold start without interest tags ===")
cold_user2 = UserProfile(user_id="cold_notag_user", username="cold_notag", is_new_user=True)
storage.add_user(cold_user2)
items2, strategy2 = rec.recommend("cold_notag_user", top_n=20)
print(f"  Cold user without tags: strategy={strategy2}, items={len(items2)}")
if items2:
    for item in items2[:5]:
        book = storage.get_book(item.book_id)
        if book:
            print(f"    {item.book_id} - {book.title} ({book.category}) [source={item.source.value}]")

print("\nAll tests completed.")
