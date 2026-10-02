"""The Operation and command catalogs list the definitions the installed parts register."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from concorde.execution.commands.catalog import COMMANDS
from concorde.execution.context import Continue, Provider, command
from concorde.execution.operations.catalog import OPERATIONS, Catalog, CatalogError
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject


def probe_step(context):
    return Continue(output={"probed": context.modules})


PROBE = Provider("probe", None, False, (probe_step,))


class CatalogTests(unittest.TestCase):
    @verifies("scenario.operations.registered")
    def test_a_registered_operation_runs_and_an_unregistered_one_is_refused(self):
        project = OperationProject(self)
        project.open_task("t1")
        with patch.dict(OPERATIONS.definitions), patch.dict(OPERATIONS.parts):
            OPERATIONS.register("prober", PROBE)
            OPERATIONS.register("prober", PROBE)
            self.assertEqual("prober", OPERATIONS.part("probe"))
            status, envelope = project.run("probe", "--task", "t1")
            self.assertEqual((0, "ok"), (status, envelope["status"]))
            self.assertEqual("probe", envelope["name"])
        from concorde.execution.runner import UsageError

        with self.assertRaises(UsageError) as raised:
            project.run("probe", "--task", "t1")
        self.assertIn("unknown operation 'probe'", str(raised.exception))
        self.assertIn("no installed part registers it", str(raised.exception))

    @verifies("scenario.operations.unique-names")
    def test_two_parts_cannot_register_one_name(self):
        for catalog, first, second in (
            (Catalog("operation"), PROBE, Provider("probe", None, True, (probe_step,))),
            (
                Catalog("command"),
                command("check-it", (probe_step,), writes=False),
                command("check-it", (probe_step,), writes=True),
            ),
        ):
            with self.subTest(kind=catalog.kind):
                catalog.register("first", first)
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("second", second)
                self.assertEqual("duplicate_definition", raised.exception.code)
                self.assertIn("first", str(raised.exception))
                self.assertIn("second", str(raised.exception))
                self.assertIs(first, catalog.get(first.name))
                # The same definition under another part is a clash too.
                with self.assertRaises(CatalogError):
                    catalog.register("second", first)

    def test_a_catalog_takes_only_definitions_of_its_kind(self):
        with self.assertRaises(CatalogError) as raised:
            Catalog("command").register("prober", PROBE)
        self.assertEqual("invalid_definition", raised.exception.code)

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


if __name__ == "__main__":
    unittest.main()
