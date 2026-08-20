import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class SelfArchitectureTests(unittest.TestCase):
    def test_concorde_hierarchy_validates_and_projects_one_level(self):
        validation = validate_project(REPOSITORY_ROOT)
        self.assertEqual(validation.status, "success", validation.findings)
        context = bounded_context(REPOSITORY_ROOT, "module.concorde")
        self.assertEqual(context.status, "success", context.findings)
        projection = context.result["context"]
        self.assertEqual(len(projection["children"]), 4)
        self.assertTrue(all("contracts" in child for child in projection["children"]))
        self.assertNotIn("feature.documentation.publish-project-docsite", repr(projection["children"]))
        refinements = {(item["from"], item["to"]) for item in projection["refinement_links"]}
        self.assertIn(("feature.distribution.package-starter-bundle", "feature.concorde.install-starter-workflow"), refinements)


if __name__ == "__main__":
    unittest.main()
