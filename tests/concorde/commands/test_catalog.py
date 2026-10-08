"""The command catalog lists the execution commands the installed parts register."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from concorde.execution.commands.catalog import COMMANDS
from concorde.execution.context import Continue, command
from concorde.execution.operations.catalog import Catalog, CatalogError
from concorde.execution.runner import UsageError, execute
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject


def check_step(context):
    return Continue(output={"checked": context.modules})


CHECK_IT = command("check-it", (check_step,), writes=False, module="module.checker")


def records(project) -> set:
    """Every file of the project's and its task worktree's Concorde records."""
    return {
        str(path)
        for root in (project.root, project.worktree("t1"))
        for path in (root / ".concorde").rglob("*")
    }


class CommandCatalogTests(unittest.TestCase):
    @verifies("scenario.commands.registered")
    def test_a_registered_command_runs(self):
        project = OperationProject(self)
        project.open_task("t1")
        with patch.dict(COMMANDS.definitions), patch.dict(COMMANDS.parts):
            COMMANDS.register("checker", CHECK_IT)
            status, envelope = project.run("check-it", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]))
        self.assertEqual(("check-it", "command"), (envelope["name"], envelope["kind"]))
        self.assertEqual({"checked": ["module.a"]}, envelope["output"])
        self.assertIsNone(envelope.get("worker"))

    @verifies("scenario.commands.listed")
    def test_a_complete_command_is_listed_with_its_module_part_and_writes(self):
        catalog = Catalog("command")
        catalog.register("checker", CHECK_IT)
        self.assertIs(CHECK_IT, catalog.get("check-it"))
        self.assertEqual(
            ("module.checker", "checker", False),
            (
                catalog.module("check-it"),
                catalog.part("check-it"),
                catalog.get("check-it").writes,
            ),
        )

    @verifies("scenario.commands.unique-names")
    def test_two_parts_cannot_register_one_command_name(self):
        different = command(
            "check-it", (check_step,), writes=True, module="module.checker"
        )
        for second in (different, CHECK_IT):
            with self.subTest(equal=second is CHECK_IT):
                catalog = Catalog("command")
                catalog.register("first", CHECK_IT)
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("second", second)
                self.assertEqual("duplicate_definition", raised.exception.code)
                self.assertIn("first", str(raised.exception))
                self.assertIn("second", str(raised.exception))
                self.assertIs(CHECK_IT, catalog.get("check-it"))
                self.assertEqual("first", catalog.part("check-it"))

    @verifies("scenario.commands.definition-complete")
    def test_an_incomplete_command_definition_is_refused(self):
        for definition in (
            command("check-it", (check_step,), writes=False),
            command("check-it", (check_step,), writes=False, module="checker"),
            command(
                "check-it",
                (check_step,),
                writes=False,
                module="module.checker",
                binding="optional",
            ),
        ):
            with self.subTest(definition=definition):
                catalog = Catalog("command")
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("checker", definition)
                self.assertEqual("invalid_definition", raised.exception.code)
                self.assertNotIn("check-it", catalog)
                self.assertEqual([], list(catalog))

    @verifies("scenario.commands.not-an-operation")
    def test_a_command_is_not_run_as_an_operation(self):
        project = OperationProject(self)
        project.open_task("t1")
        with patch.dict(COMMANDS.definitions), patch.dict(COMMANDS.parts):
            COMMANDS.register("checker", CHECK_IT)
            before = records(project)
            with self.assertRaises(UsageError) as raised:
                execute("operation", "check-it", [], cwd=project.worktree("t1"))
        self.assertIn("check-it is a command, not an Operation", str(raised.exception))
        self.assertIn("`concorde check-it`", str(raised.exception))
        self.assertEqual(before, records(project))


if __name__ == "__main__":
    unittest.main()
