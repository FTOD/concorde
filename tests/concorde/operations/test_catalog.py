"""The Operation and command catalogs list the definitions the installed parts register."""

from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from concorde.execution.commands.catalog import COMMANDS
from concorde.execution.context import Continue, Provider
from concorde.execution.operations.catalog import OPERATIONS, Catalog, CatalogError
from concorde.execution.runner import UsageError
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject


def probe_step(context):
    return Continue(output={"probed": context.modules})


PROBE = Provider("probe", None, False, (probe_step,), module="module.prober")


def records(project) -> set:
    """Every file of the project's and its task worktrees' Concorde records."""
    return {
        str(path)
        for root in (project.root, project.worktree("t1"))
        for path in (root / ".concorde").rglob("*")
    }


class CatalogTests(unittest.TestCase):
    @verifies("scenario.operations.registered")
    def test_a_registered_operation_runs(self):
        project = OperationProject(self)
        project.open_task("t1")
        with patch.dict(OPERATIONS.definitions), patch.dict(OPERATIONS.parts):
            OPERATIONS.register("prober", PROBE)
            status, envelope = project.run("probe", "--task", "t1")
            self.assertEqual((0, "ok"), (status, envelope["status"]))
            self.assertEqual("probe", envelope["name"])
            self.assertEqual({"probed": ["module.a"]}, envelope["output"])

    @verifies("scenario.operations.repeated")
    def test_the_same_part_may_register_the_same_definition_again(self):
        catalog = Catalog("operation")
        catalog.register("prober", PROBE)
        catalog.register("prober", replace(PROBE))
        self.assertIs(PROBE, catalog.get("probe"))
        self.assertEqual("prober", catalog.part("probe"))
        self.assertEqual(["probe"], list(catalog))

    @verifies("scenario.operations.unknown")
    def test_an_unregistered_operation_is_a_command_line_error(self):
        project = OperationProject(self)
        project.open_task("t1")
        self.assertNotIn("probe", OPERATIONS)
        before = records(project)
        with self.assertRaises(UsageError) as raised:
            project.run("probe", "--task", "t1")
        self.assertIn("unknown operation 'probe'", str(raised.exception))
        self.assertIn("no installed part registers it", str(raised.exception))
        # No run began: nothing was recorded anywhere.
        self.assertEqual(before, records(project))

    @verifies("scenario.operations.unique-names")
    def test_two_parts_cannot_register_one_name(self):
        different = Provider("probe", None, True, (probe_step,), module="module.prober")
        for second in (different, PROBE):
            with self.subTest(equal=second is PROBE):
                catalog = Catalog("operation")
                catalog.register("first", PROBE)
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("second", second)
                self.assertEqual("duplicate_definition", raised.exception.code)
                self.assertIn("first", str(raised.exception))
                self.assertIn("second", str(raised.exception))
                self.assertIs(PROBE, catalog.get("probe"))
                self.assertEqual("first", catalog.part("probe"))
        # The registering part's own changed definition is a clash too.
        catalog = Catalog("operation")
        catalog.register("first", PROBE)
        with self.assertRaises(CatalogError):
            catalog.register("first", different)
        self.assertIs(PROBE, catalog.get("probe"))

    def test_a_catalog_takes_only_definitions_of_its_kind(self):
        with self.assertRaises(CatalogError) as raised:
            Catalog("command").register("prober", PROBE)
        self.assertEqual("invalid_definition", raised.exception.code)

    @verifies("scenario.operations.definition-complete")
    def test_an_incomplete_operation_definition_is_refused(self):
        for definition in (
            replace(PROBE, module=None),
            replace(PROBE, module="method"),
            replace(PROBE, workers=()),
            replace(PROBE, workers=("",)),
            replace(PROBE, workers=("worker", "")),
            replace(PROBE, workers=("worker", None)),
        ):
            with self.subTest(definition=definition):
                catalog = Catalog("operation")
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("prober", definition)
                self.assertEqual("invalid_definition", raised.exception.code)
                self.assertNotIn(definition.name, catalog)
                self.assertEqual([], list(catalog))

    @verifies("scenario.operations.listed")
    def test_a_complete_definition_is_listed_with_its_module_and_part(self):
        catalog = Catalog("operation")
        catalog.register("prober", PROBE)
        self.assertEqual(
            ("module.prober", "prober"),
            (catalog.module("probe"), catalog.part("probe")),
        )

    @verifies("scenario.operations.listed")
    def test_method_registers_its_definitions(self):
        from concorde.method import registration

        self.assertEqual(
            sorted(item.name for item in registration.DEFINED_OPERATIONS),
            sorted(name for name in OPERATIONS if OPERATIONS.part(name) == "method"),
        )
        self.assertEqual(
            ["delivery", "scaffold", "task-validation"],
            sorted(name for name in COMMANDS if COMMANDS.part(name) == "method"),
        )
        # Each with the Module of the method part that provides it.
        self.assertEqual(
            {
                "understand": "module.understanding",
                "plan_review": "module.understanding",
                "specify": "module.specification",
                "implement": "module.implementation",
                "test": "module.implementation",
                "spec_panel": "module.spec-review",
                "code_review": "module.code-review",
                "project_review": "module.project-review",
                "survey": "module.adoption",
                "code_to_spec": "module.adoption",
                "general": "module.general-work",
                "task-validation": "module.validation",
                "delivery": "module.delivery",
                "scaffold": "module.scaffold",
            },
            {
                **{name: OPERATIONS.module(name) for name in OPERATIONS},
                **{name: COMMANDS.module(name) for name in COMMANDS},
            },
        )


if __name__ == "__main__":
    unittest.main()
