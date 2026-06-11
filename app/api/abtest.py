from fastapi import APIRouter

from app.abtest.manager import get_abtest_manager
from app.abtest.scheduler import get_scheduler_manager

router = APIRouter(prefix="/abtest", tags=["abtest"])


@router.get("/status")
def get_abtest_status():
    abtest = get_abtest_manager()
    return abtest.get_comparison()


@router.post("/start")
def start_abtest(old_model: str = "v1", new_model: str = "v2"):
    abtest = get_abtest_manager()
    abtest.start_test(old_model, new_model)
    return {"status": "ok", "message": f"AB test started: {old_model} vs {new_model}"}


@router.post("/advance")
def advance_phase():
    abtest = get_abtest_manager()
    abtest.advance_phase()
    return {"status": "ok", "phase": abtest.get_state().current_phase.value}


@router.get("/user-group/{user_id}")
def get_user_group(user_id: str):
    abtest = get_abtest_manager()
    group = abtest.assign_user_group(user_id)
    return {"user_id": user_id, "group": group}


@router.post("/scheduler/run-now")
def run_scheduler_now():
    scheduler = get_scheduler_manager()
    scheduler.run_weekly_now()
    return {"status": "ok", "message": "Weekly task executed"}


@router.post("/scheduler/start")
def start_scheduler():
    scheduler = get_scheduler_manager()
    scheduler.start()
    return {"status": "ok", "message": "Scheduler started"}


@router.post("/scheduler/stop")
def stop_scheduler():
    scheduler = get_scheduler_manager()
    scheduler.shutdown()
    return {"status": "ok", "message": "Scheduler stopped"}
