from pydantic import BaseModel, Field
from typing import Optional, Dict
from enum import Enum
from datetime import datetime


class ABPhase(str, Enum):
    phase_1 = "phase_1"
    phase_2 = "phase_2"
    phase_3 = "phase_3"
    phase_4 = "phase_4"
    completed = "completed"


class ABTestState(BaseModel):
    current_phase: ABPhase = ABPhase.phase_1
    start_time: Optional[datetime] = None
    old_model_weight: float = 0.7
    new_model_weight: float = 0.3
    old_model_name: str = "v1"
    new_model_name: str = "v2"
    weekly_stats_old: Dict[str, float] = Field(default_factory=dict)
    weekly_stats_new: Dict[str, float] = Field(default_factory=dict)

    def get_weights(self):
        return {
            "old": self.old_model_weight,
            "new": self.new_model_weight,
        }
