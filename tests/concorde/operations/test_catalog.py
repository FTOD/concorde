"""The Operation and command catalogs list the definitions the installed parts register."""

from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from concorde.execution.commands.catalog import COMMANDS
from concorde.execution.context import Continue, Provider, command
from concorde.execution.operations.catalog import OPERATIONS, Catalog, CatalogError
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject


def probe_step(context):
    return Continue(output={"probed": context.modules})


PROBE = Provider("probe", None, False, (probe_step,), module="module.prober")


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
            (
                Catalog("operation"),
                PROBE,
                Provider("probe", None, True, (probe_step,), module="module.prober"),
            ),
            (
                Catalog("command"),
                command("check-it", (probe_step,), writes=False, module="module.a"),
                command("check-it", (probe_step,), writes=True, module="module.a"),
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

    @verifies("scenario.operations.definition-complete")
    def test_a_definition_names_its_providing_module_and_an_operation_its_workers(self):
        for catalog, definition in (
            (Catalog("operation"), replace(PROBE, module=None)),
            (Catalog("operation"), replace(PROBE, module="method")),
            (Catalog("operation"), replace(PROBE, workers=())),
            (Catalog("command"), command("check-it", (probe_step,), writes=False)),
        ):
            with self.subTest(definition=definition):
                with self.assertRaises(CatalogError) as raised:
                    catalog.register("prober", definition)
                self.assertEqual("invalid_definition", raised.exception.code)
                self.assertNotIn(definition.name, catalog)
        catalog = Catalog("operation")
        catalog.register("prober", PROBE)
        self.assertEqual(
            ("module.prober", "prober"),
            (catalog.module("probe"), catalog.part("probe")),
        )

    @verifies("scenario.operations.definition-complete")
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
                "spec_review": "module.spec-review",
                "spec_panel": "module.spec-review",
                "code_review": "module.code-review",
                "survey": "module.adoption",
                "code_to_spec": "module.adoption",
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
