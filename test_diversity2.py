import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage.memory_store import get_storage
from app.rec.hybrid import HybridRecommender

storage = get_storage()
rec = HybridRecommender()

def check_no_3_consecutive(items, label):
    cats = []
    for item in items:
        book = storage.get_book(item.book_id)
        cats.append(book.category if book else "?")
    violations = []
    for i in range(len(cats) - 2):
        if cats[i] == cats[i+1] == cats[i+2]:
            violations.append((i, cats[i]))
    return violations

print("=== Cold start with interest tags - diversity check ===")
from app.models.user import UserProfile
cold_user = UserProfile(user_id="cold_diverse", username="cold_diverse", is_new_user=True, interest_tags=["科幻", "言情", "历史"])
storage.add_user(cold_user)

items, strategy = rec.recommend("cold_diverse", top_n=20)
print(f"Strategy: {strategy}, items: {len(items)}")

cats = []
for item in items:
    book = storage.get_book(item.book_id)
    cat = book.category if book else "?"
    cats.append(cat)
    print(f"  {item.book_id} - {book.title if book else '?'} ({cat})")

violations = check_no_3_consecutive(items, "cold_diverse")
if violations:
    print(f"  FAIL: {len(violations)} violations")
else:
    print(f"  PASS: no 3-consecutive violations")

print(f"\n=== Hot fallback diversity (full scan) ===")
all_pass = True
from app.rec.collaborative import get_collaborative_filtering
cf = get_collaborative_filtering()
for u in storage.get_all_users():
    items, strategy = rec.recommend(u.user_id, top_n=20)
    v = check_no_3_consecutive(items, f"{u.user_id}/{strategy}")
    if v:
        all_pass = False
        print(f"  FAIL: {u.user_id} ({strategy}) - {len(v)} violations")
        for pos, cat in v:
            print(f"    pos {pos}-{pos+2}: all '{cat}'")

if all_pass:
    print("  ALL PASS: no user has 3-consecutive violations")
