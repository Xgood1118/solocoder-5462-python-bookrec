from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.storage.memory_store import get_storage
from app.rec.hybrid import get_hybrid_recommender
from app.feedback.manager import get_feedback_manager
from app.abtest.manager import get_abtest_manager
from app.config import get_settings


class SchedulerManager:
    def __init__(self):
        self.settings = get_settings()
        self.storage = get_storage()
        self.hybrid_rec = get_hybrid_recommender()
        self.feedback = get_feedback_manager()
        self.abtest = get_abtest_manager()
        self.scheduler = BackgroundScheduler()
        self._scheduled = False

    def _weekly_task(self):
        print(f"[{datetime.now()}] Running weekly scheduled task...")

        self.hybrid_rec.refresh_all()
        print(f"[{datetime.now()}] Model refreshed")

        weekly_stats = self.feedback.get_weekly_stats()
        print(f"[{datetime.now()}] Weekly stats: {weekly_stats}")

        self.abtest.advance_phase()
        print(f"[{datetime.now()}] AB test phase advanced to {self.abtest.get_state().current_phase}")

        self.storage.save_to_seed()
        print(f"[{datetime.now()}] Data saved to seed files")

    def start(self):
        if self._scheduled:
            return

        trigger = CronTrigger(day_of_week="sun", hour=3, minute=0)
        self.scheduler.add_job(
            self._weekly_task,
            trigger=trigger,
            id="weekly_maintenance",
            replace_existing=True,
        )

        self.scheduler.start()
        self._scheduled = True
        print("Scheduler started. Weekly task scheduled for Sunday 3:00 AM.")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._scheduled = False
            print("Scheduler stopped.")

    def run_weekly_now(self):
        self._weekly_task()


_scheduler_instance = None


def get_scheduler_manager() -> SchedulerManager:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerManager()
    return _scheduler_instance
