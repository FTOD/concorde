"""An Operation's run checks all its workers against the model map before the first launches."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from concorde.kernel.errors import ERROR_SCHEMA
from concorde.execution.context import Continue, Provider
from concorde.worker_harness import models
from concorde.execution.operations import catalog
from concorde.method.spec_review.panel import WORKERS
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject


def panel_step(context):
    """Stands in for the panel's steps, which would launch its workers."""
    return Continue(output={"reached": True})


PANEL = Provider("spec_panel", "review-spec", False, (panel_step,), workers=WORKERS)
NO_WORKERS = Provider("spec_panel", None, False, (panel_step,), workers=())


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")
        patcher = patch.dict(catalog.CATALOG, {"spec_panel": f"{__name__}:PANEL"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def configure(self, workers: dict) -> None:
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"sonnet": {}, "fast": {}},
                    "default": {"backend": "claude", "model": "sonnet"},
                    "operations": {"spec_panel": {"workers": workers}},
                }
            )
        )

    @verifies("scenario.operations.worker-models-checked-at-admission")
    def test_every_worker_is_checked_against_the_map_before_the_first_launches(self):
        # The test model map gives `fast` a pi id only.
        self.configure({"reviewer1": {"model": "fast"}, "chair": {"model": "fast"}})
        status, envelope = self.project.run("spec_panel", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertIsNone(envelope["output"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("worker_model_unavailable", envelope["error"]["code"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual(
            ("model_unmapped", "environment"),
            (cause["code"], cause["unhandled"]["reason"]),
        )
        self.assertIn(
            "`models.fast.claude` (for spec_panel/reviewer1, spec_panel/chair)",
            cause["detail"],
        )
        self.assertTrue(
            any("model map" in option for option in envelope["error"]["options"])
        )
        validate(envelope["error"], ERROR_SCHEMA)
        # Once the map can place every worker, the run goes on to its own steps.
        self.configure({"reviewer1": {"model": "fast", "backend": "pi"}})
        status, envelope = self.project.run("spec_panel", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual({"reached": True}, envelope["output"])

    def test_a_definition_without_workers_is_not_checked(self):
        self.assertEqual(
            "check_worker_models", catalog.provider("spec_panel").steps[0].__name__
        )
        with patch.dict(
            catalog.CATALOG,
            {"spec_panel": f"{__name__}:NO_WORKERS"},
        ):
            self.assertEqual((panel_step,), catalog.provider("spec_panel").steps)


if __name__ == "__main__":
    unittest.main()
