"""Capability modules (top-level ``capabilities/``) must agree with the contract tables in
``protocol_contracts.py`` (proposal section 6, Stage B1 item 2).

This uses ``protocol_contracts.load_capability_inventory()`` rather than a bare
``import capabilities``: under ``unittest discover -s tests/concorde``, discovery itself imports
``tests/concorde/capabilities/__init__.py`` as top-level module ``capabilities`` while walking the
tree, which would otherwise permanently shadow the real repository-root package for this process.
"""
from __future__ import annotations

import importlib
import sys
import unittest

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.protocol_contracts import (  # noqa: E402
    COMPOSITE_OPERATIONS,
    GLOBAL_OPERATIONS,
    INTERNAL_OPERATIONS,
    LIFECYCLE_OPERATIONS,
    MAIN_ROUTED_OPERATIONS,
    OPERATIONS,
    PUBLIC_OPERATIONS,
    dependencies,
    load_capability_inventory,
    schemas,
)

capabilities = load_capability_inventory()


def _modules():
    return {name: importlib.import_module(f"{capabilities.__name__}.{name}") for name in capabilities.CAPABILITIES}


class CapabilityModuleContractTests(unittest.TestCase):
    def test_capability_names_match_the_operation_registry_exactly(self):
        external_names = {capabilities.external_name(name) for name in capabilities.CAPABILITIES}
        self.assertEqual(external_names, set(OPERATIONS))
        self.assertEqual(len(capabilities.CAPABILITIES), len(set(capabilities.CAPABILITIES)))

    def test_external_name_helper_is_the_only_naming_rule(self):
        for name in capabilities.CAPABILITIES:
            module = importlib.import_module(f"{capabilities.__name__}.{name}")
            self.assertEqual(module.EXTERNAL_NAME, capabilities.external_name(name))
            self.assertEqual(module.EXTERNAL_NAME, "concorde-" + name.replace("_", "-"))

    def test_class_matches_the_global_lifecycle_stage_partition(self):
        modules = _modules()
        for name, module in modules.items():
            external = module.EXTERNAL_NAME
            if external in GLOBAL_OPERATIONS:
                self.assertEqual(module.CLASS, "global", external)
            elif external in LIFECYCLE_OPERATIONS:
                self.assertEqual(module.CLASS, "lifecycle", external)
            elif external in INTERNAL_OPERATIONS:
                self.assertEqual(module.CLASS, "stage", external)
            else:
                self.fail(f"{external} is not classified by any known operation partition")
        self.assertEqual(
            {name for name, module in modules.items() if module.CLASS == "global"},
            {name for name in capabilities.CAPABILITIES if capabilities.external_name(name) in GLOBAL_OPERATIONS},
        )

    def test_roles_and_uses_match_dependencies_exactly(self):
        # dependencies() is the deterministic policy source, historically a flattened mix of role
        # identities and (for a composing capability) the external names of the capabilities it
        # composes. A module's own declared (ROLES, USES) must reconstruct it exactly: the roles
        # it launches itself, plus the external name of every capability it USES, plus (for a
        # main-routed capability other than main itself) the coordinator role main already grants.
        modules = _modules()
        for name, module in modules.items():
            external = module.EXTERNAL_NAME
            declared_roles = {"concorde-" + role.name.replace("_", "-") for role in module.ROLES}
            used_names = {capabilities.external_name(used) for used in module.USES}
            expected = declared_roles | used_names
            if external in MAIN_ROUTED_OPERATIONS and external != "concorde-main":
                expected = expected | {"concorde-coordinator"}
            self.assertEqual(set(dependencies(external)), expected, f"{external}: (ROLES, USES) do not reconstruct dependencies()")

    def test_uses_matches_the_declared_composition(self):
        expected = {
            "main": (),
            "dev_loop": ("specify", "review", "plan", "tasks", "implement", "validate"),
            "reflections_triage": ("dev_loop",),
            "init": (),
            "configure": (),
            "validate": (),
            "deliver": (),
            "specify": (),
            "review": (),
            "context_solve": (),
            "plan": (),
            "tasks": (),
            "implement": (),
        }
        modules = _modules()
        self.assertEqual({name: module.USES for name, module in modules.items()}, expected)
        self.assertEqual(
            set(COMPOSITE_OPERATIONS),
            {capabilities.external_name(name) for name, module in modules.items() if module.USES},
        )

    def test_every_use_names_a_declared_capability(self):
        for name in capabilities.CAPABILITIES:
            module = importlib.import_module(f"{capabilities.__name__}.{name}")
            for used in module.USES:
                self.assertIn(used, capabilities.CAPABILITIES, f"{name}.USES names unknown capability {used!r}")

    def test_uses_graph_is_acyclic(self):
        modules = _modules()
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name, chain):
            if name in visiting:
                self.fail(f"cycle in capability USES graph: {' -> '.join(chain + (name,))}")
            if name in visited:
                return
            visiting.add(name)
            for used in modules[name].USES:
                visit(used, chain + (name,))
            visiting.discard(name)
            visited.add(name)

        for name in capabilities.CAPABILITIES:
            visit(name, ())

    def test_request_and_response_are_exactly_the_exported_schemas(self):
        exported = schemas()
        for name in capabilities.CAPABILITIES:
            module = importlib.import_module(f"{capabilities.__name__}.{name}")
            self.assertEqual(module.REQUEST, exported[f"{module.EXTERNAL_NAME}-request"])
            self.assertEqual(module.RESPONSE, exported[f"{module.EXTERNAL_NAME}-response"])

    def test_public_capabilities_have_no_module_declared_import_cycle(self):
        # Capability modules import only roles/contract_shapes/wire_shapes at module load time
        # (operation_service is imported lazily inside run()); importing every module and calling
        # its run() attribute (without invoking it) exercises that this loads cleanly.
        for name in capabilities.CAPABILITIES:
            module = importlib.import_module(f"{capabilities.__name__}.{name}")
            self.assertTrue(callable(module.run))

    def test_main_routed_operations_match_the_global_class(self):
        self.assertEqual(set(MAIN_ROUTED_OPERATIONS), {"concorde-main", "concorde-dev-loop"})
        self.assertTrue(set(MAIN_ROUTED_OPERATIONS).issubset(GLOBAL_OPERATIONS))

    def test_every_public_capability_class_is_global_or_lifecycle(self):
        modules = _modules()
        for name, module in modules.items():
            if module.EXTERNAL_NAME in PUBLIC_OPERATIONS:
                self.assertIn(module.CLASS, {"global", "lifecycle"}, module.EXTERNAL_NAME)
            else:
                self.assertEqual(module.CLASS, "stage", module.EXTERNAL_NAME)


if __name__ == "__main__":
    unittest.main()
