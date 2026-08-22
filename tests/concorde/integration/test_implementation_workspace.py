import json
import os
import subprocess
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


FEATURE_RELATIVE = "specs/concorde/features/001-concorde-starter-workflow"


class ImplementationWorkspaceIntegration(unittest.TestCase):
    def test_feature_paths_separate_durable_intent_from_delivery_attempt(self):
        environment = os.environ.copy()
        environment["SPECIFY_FEATURE_DIRECTORY"] = FEATURE_RELATIVE

        completed = subprocess.run(
            [
                str(REPOSITORY_ROOT / ".specify/scripts/bash/check-prerequisites.sh"),
                "--json",
                "--paths-only",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = json.loads(completed.stdout)
        feature_root = REPOSITORY_ROOT / FEATURE_RELATIVE
        implementation = feature_root / "implementation"

        self.assertEqual(paths["FEATURE_SPEC"], str(feature_root / "spec.md"))
        self.assertEqual(paths["IMPLEMENTATION_DIR"], str(implementation))
        self.assertEqual(paths["IMPL_PLAN"], str(implementation / "plan.md"))
        self.assertEqual(paths["TASKS"], str(implementation / "tasks.md"))
        self.assertFalse((feature_root / "plan.md").exists())
        self.assertFalse((feature_root / "tasks.md").exists())


if __name__ == "__main__":
    unittest.main()
