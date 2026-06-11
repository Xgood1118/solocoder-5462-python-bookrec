import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import get_settings
    print("✓ config module OK")
    settings = get_settings()
    print(f"  port: {settings.port}")
except Exception as e:
    print(f"✗ config module FAILED: {e}")

try:
    from app.models.user import UserProfile, BorrowRecord
    from app.models.book import BookFeature
    print("✓ models module OK")
except Exception as e:
    print(f"✗ models module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.storage.memory_store import get_storage
    storage = get_storage()
    print(f"✓ storage module OK (users: {len(storage.users)}, books: {len(storage.books)})")
except Exception as e:
    print(f"✗ storage module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.feature.engineer import compute_interaction_score, extract_keywords
    print("✓ feature module OK")
except Exception as e:
    print(f"✗ feature module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.rec.collaborative import get_collaborative_filtering
    cf = get_collaborative_filtering()
    print("✓ collaborative module OK")
except Exception as e:
    print(f"✗ collaborative module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.rec.content_based import get_content_recommender
    content = get_content_recommender()
    print("✓ content_based module OK")
except Exception as e:
    print(f"✗ content_based module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.rec.knowledge_graph import get_graph_recommender
    graph = get_graph_recommender()
    print("✓ knowledge_graph module OK")
except Exception as e:
    print(f"✗ knowledge_graph module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.rec.hybrid import get_hybrid_recommender
    hybrid = get_hybrid_recommender()
    print("✓ hybrid module OK")
except Exception as e:
    print(f"✗ hybrid module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.feedback.manager import get_feedback_manager
    fb = get_feedback_manager()
    print("✓ feedback module OK")
except Exception as e:
    print(f"✗ feedback module FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.abtest.manager import get_abtest_manager
    ab = get_abtest_manager()
    print("✓ abtest module OK")
except Exception as e:
    print(f"✗ abtest module FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nAll module imports checked.")
