from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    port: int = 8000
    data_dir: str = "./data"
    hot_book_top_n: int = 50
    collab_k: int = 20
    collab_weight: float = 0.5
    content_weight: float = 0.3
    graph_weight: float = 0.2
    similarity_threshold: float = 0.1
    pmi_threshold: float = 0.5
    diversity_window: int = 3
    serendipity_ratio: float = 0.1
    abtest_duration_weeks: int = 4

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
