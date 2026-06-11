import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.feedback import FeedbackType
from app.models.user import BorrowRecord

print("=== Test 1: FeedbackType with Chinese values ===")
for val in ["like", "dislike", "already_read", "喜欢", "不感兴趣", "已读过"]:
    try:
        ft = FeedbackType(val)
        print(f"  ✓ '{val}' -> {ft.value}")
    except Exception as e:
        print(f"  ✗ '{val}' failed: {e}")

print("\n=== Test 2: BorrowRecord without borrow_time ===")
try:
    record = BorrowRecord(book_id="b0001", read_completion=0.8, read_duration=3600, rating=4.5)
    print(f"  ✓ BorrowRecord created, borrow_time={record.borrow_time}")
except Exception as e:
    print(f"  ✗ BorrowRecord failed: {e}")

print("\n=== Test 3: Full module import check ===")
try:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    print("  ✓ All modules imported")

    resp = client.get("/users/u0001")
    print(f"  GET /users/u0001 -> {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"    user: {data['username']}, borrow_count: {data['total_borrow_count']}")

    resp = client.get("/users/u0001/borrow-history")
    print(f"  GET /users/u0001/borrow-history -> {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"    history count: {len(data)}")
        if data:
            print(f"    first: book_id={data[0]['book_id']}, completion={data[0]['read_completion']}")

    print("\n=== Test 4: Borrow book ===")
    resp = client.post("/users", json={"user_id": "u_test_borrow", "username": "测试借书用户"})
    print(f"  POST /users (create) -> {resp.status_code}")

    resp = client.get("/books/hot/list")
    if resp.status_code == 200:
        books = resp.json()
        if books:
            test_book_id = books[0]["book_id"]
            print(f"  Test book: {test_book_id} ({books[0]['title']})")
            borrow_payload = {
                "book_id": test_book_id,
                "read_completion": 0.75,
                "read_duration": 5400,
                "rating": 4.2,
                "comment": "测试借书评论",
            }
            resp = client.post(f"/users/u_test_borrow/borrow", json=borrow_payload)
            print(f"  POST /users/u_test_borrow/borrow -> {resp.status_code}")
            if resp.status_code != 200:
                print(f"    detail: {resp.text}")
            else:
                data = resp.json()
                print(f"    updated borrow_count: {data['total_borrow_count']}")

                resp = client.get(f"/users/u_test_borrow/borrow-history")
                print(f"  GET /users/u_test_borrow/borrow-history -> {resp.status_code}")
                if resp.status_code == 200:
                    history = resp.json()
                    print(f"    history count: {len(history)}")
                    if history:
                        print(f"    book: {history[0]['book_id']}, rating: {history[0]['rating']}")

    print("\n=== Test 5: Feedback with Chinese labels ===")
    for label in ["喜欢", "不感兴趣", "已读过"]:
        payload = {"user_id": "u0001", "book_id": "b0001", "feedback_type": label}
        resp = client.post("/feedback", json=payload)
        print(f"  POST /feedback ({label}) -> {resp.status_code}")
        if resp.status_code != 200:
            print(f"    detail: {resp.text}")

    resp = client.get("/feedback/u0001/summary")
    print(f"  GET /feedback/u0001/summary -> {resp.status_code}")
    if resp.status_code == 200:
        print(f"    summary: {resp.json()}")

    print("\n=== All tests completed ===")

except ImportError as e:
    print(f"  TestClient not available ({e}), skipping HTTP tests")
except Exception as e:
    import traceback
    traceback.print_exc()
