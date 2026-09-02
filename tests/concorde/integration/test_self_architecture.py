import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402
from concorde.repository import ProjectRepository  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class SelfArchitectureTests(unittest.TestCase):
    def test_concorde_has_six_recursive_profile_seven_architectures(self):
        package = ProjectRepository(REPOSITORY_ROOT).load()
        modules = package.documents("module")
        self.assertEqual(len(modules), 6)
        self.assertEqual({module.identifier for module in modules}, {
            "module.concorde", "module.concorde.commands", "module.concorde.runtime",
            "module.concorde.workspace", "module.concorde.distribution", "module.concorde.auto-docs",
        })
        self.assertTrue(all(module.path.endswith("architecture.md") for module in modules))

    def test_concorde_hierarchy_validates_and_projects_one_level(self):
        validation = validate_project(REPOSITORY_ROOT)
        self.assertEqual(validation.status, "success", validation.findings)
        context = bounded_context(REPOSITORY_ROOT, "module.concorde")
        self.assertEqual(context.status, "success", context.findings)
        projection = context.result["context"]
        self.assertEqual(len(projection["children"]), 5)
        self.assertTrue(all("architecture" in child for child in projection["children"]))
        self.assertTrue(projection["current_module"]["entities"])
        self.assertTrue(projection["current_module"]["relationships"])
        self.assertTrue(projection["current_module"]["interactions"])
        self.assertNotIn("module.concorde.auto-docs", repr(projection["children"][0]))

    def test_source_specs_have_no_legacy_durable_artifacts(self):
        specification = REPOSITORY_ROOT / "specs/concorde"
        self.assertFalse(list(specification.rglob("module.md")))
        self.assertFalse(list(specification.rglob("abstract.md")))
        self.assertFalse(list(specification.rglob("implementation.md")))
        self.assertFalse(list(specification.rglob("contract.md")))
        self.assertFalse(list(specification.rglob("reflections.md")))
        self.assertFalse([path for path in specification.rglob("*") if path.is_dir() and path.name in {"attempts", "contracts", "subfeatures"}])


if __name__ == "__main__":
    unittest.main()
