from typing import Dict, Optional
from datetime import datetime, timedelta
import random

from app.models.abtest import ABTestState, ABPhase
from app.config import get_settings
from app.storage.memory_store import get_storage
from app.rec.hybrid import get_hybrid_recommender
from app.feedback.manager import get_feedback_manager


class ABTestManager:
    def __init__(self):
        self.settings = get_settings()
        self.storage = get_storage()
        self.hybrid_rec = get_hybrid_recommender()
        self.feedback = get_feedback_manager()
        self.state = ABTestState()
        self.user_groups: Dict[str, str] = {}
        self.weekly_stats_old: Dict[str, float] = {}
        self.weekly_stats_new: Dict[str, float] = {}

    def start_test(self, old_model_name: str = "v1", new_model_name: str = "v2"):
        self.state = ABTestState(
            current_phase=ABPhase.phase_1,
            start_time=datetime.now(),
            old_model_weight=0.7,
            new_model_weight=0.3,
            old_model_name=old_model_name,
            new_model_name=new_model_name,
        )
        self.user_groups.clear()
        self.weekly_stats_old.clear()
        self.weekly_stats_new.clear()

    def assign_user_group(self, user_id: str) -> str:
        if user_id in self.user_groups:
            return self.user_groups[user_id]

        new_weight = self.state.new_model_weight
        group = "new" if random.random() < new_weight else "old"
        self.user_groups[user_id] = group
        return group

    def advance_phase(self):
        phases = [
            (ABPhase.phase_1, 0.7, 0.3),
            (ABPhase.phase_2, 0.5, 0.5),
            (ABPhase.phase_3, 0.3, 0.7),
            (ABPhase.phase_4, 0.0, 1.0),
        ]

        current_idx = None
        for i, (phase, _, _) in enumerate(phases):
            if phase == self.state.current_phase:
                current_idx = i
                break

        if current_idx is None or current_idx >= len(phases) - 1:
            self.state.current_phase = ABPhase.completed
            self.state.old_model_weight = 0.0
            self.state.new_model_weight = 1.0
        else:
            next_phase, old_w, new_w = phases[current_idx + 1]
            self.state.current_phase = next_phase
            self.state.old_model_weight = old_w
            self.state.new_model_weight = new_w

    def get_state(self) -> ABTestState:
        return self.state

    def record_group_metric(self, group: str, metric: str, value: float):
        if group == "old":
            self.weekly_stats_old[metric] = self.weekly_stats_old.get(metric, 0.0) + value
        else:
            self.weekly_stats_new[metric] = self.weekly_stats_new.get(metric, 0.0) + value

    def get_comparison(self) -> Dict:
        return {
            "phase": self.state.current_phase.value,
            "old_model": self.state.old_model_name,
            "new_model": self.state.new_model_name,
            "old_weight": self.state.old_model_weight,
            "new_weight": self.state.new_model_weight,
            "old_stats": dict(self.weekly_stats_old),
            "new_stats": dict(self.weekly_stats_new),
            "is_completed": self.state.current_phase == ABPhase.completed,
        }


_abtest_instance = None


def get_abtest_manager() -> ABTestManager:
    global _abtest_instance
    if _abtest_instance is None:
        _abtest_instance = ABTestManager()
    return _abtest_instance
