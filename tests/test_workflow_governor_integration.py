import unittest
from sqlalchemy import delete

from app.database import Base, SessionLocal, engine
from app.models.entities import CorrectionQueue, Metric, Project, Signal, Task, WeeklyProfile
from app.models.schemas import ProjectCreate, TaskCreate
from app.services.profile_service import live_constitutional_snapshot, persist_weekly_profile
from app.services.workflow_service import apply_corrections, plan_project, queued_corrections, route_task


class TestWorkflowGovernorIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        with SessionLocal() as db:
            for model in (Metric, CorrectionQueue, WeeklyProfile, Task, Signal, Project):
                db.execute(delete(model))
            db.commit()

    def test_route_task_inherits_governor_bias(self):
        with SessionLocal() as db:
            project = plan_project(
                db,
                ProjectCreate(
                    id="p1",
                    name="Governor Build",
                    objective="Build a constitutional adaptive governor",
                    steps=["design", "implement", "test"],
                    risks=["metric drift"],
                    success_criteria=["M >= tau"],
                ),
            )
            snapshot = live_constitutional_snapshot(db)
            task, meta = route_task(
                db,
                TaskCreate(
                    id="t1",
                    title="Refine routing",
                    project_id=project.id,
                    status="Todo",
                    from_signal=True,
                    task_type="architecture",
                ),
                governor_snapshot=snapshot,
            )
            self.assertTrue(meta["governor_applied"])
            self.assertEqual(task.mode, "Analytical")
            self.assertTrue(task.has_metric)
            self.assertEqual(task.priority, "High")

    def test_invalid_task_queues_and_correction_creates_remediation(self):
        with SessionLocal() as db:
            project = plan_project(
                db,
                ProjectCreate(
                    id="p2",
                    name="Recovery Project",
                    objective="Repair invalid task flow",
                    steps=["audit", "repair"],
                    risks=["bad task inputs"],
                    success_criteria=["queue drains"],
                ),
            )
            snapshot = live_constitutional_snapshot(db)
            task, _ = route_task(
                db,
                TaskCreate(
                    id="bad-1",
                    title="Broken task",
                    project_id=project.id,
                    task_type="repair",
                ),
                governor_snapshot=snapshot,
            )
            self.assertTrue(task.is_invalid)
            self.assertTrue(task.correction_queue)
            self.assertEqual(len(queued_corrections(db)), 1)

            created = apply_corrections(db, snapshot, limit=5)
            self.assertEqual(created[0]["id"], "corr-bad-1")
            self.assertEqual(len(queued_corrections(db)), 0)

    def test_weekly_profile_is_persisted(self):
        with SessionLocal() as db:
            snapshot = live_constitutional_snapshot(db)
            weekly = persist_weekly_profile(db, snapshot)
            self.assertEqual(weekly.id, f"weekly-{weekly.week_start.isoformat()}")
            self.assertEqual(db.get(WeeklyProfile, weekly.id).id, weekly.id)


if __name__ == "__main__":
    unittest.main()
