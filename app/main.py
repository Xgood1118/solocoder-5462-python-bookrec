from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.users import router as users_router
from app.api.books import router as books_router
from app.api.recommend import router as recommend_router
from app.api.feedback import router as feedback_router
from app.api.abtest import router as abtest_router
from app.config import get_settings
from app.abtest.scheduler import get_scheduler_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = get_scheduler_manager()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Book Recommendation Service",
    description="在线读书平台图书推荐后端服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)
app.include_router(books_router)
app.include_router(recommend_router)
app.include_router(feedback_router)
app.include_router(abtest_router)


@app.get("/")
def root():
    settings = get_settings()
    return {
        "service": "Book Recommendation Service",
        "version": "1.0.0",
        "port": settings.port,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
