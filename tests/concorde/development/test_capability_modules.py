"""Capability modules (top-level ``capabilities/``) must agree with the contract tables in
``contracts.py`` (proposal section 6, Stage B1 item 2).

This uses ``contracts.load_capability_inventory()`` rather than a bare
``import capabilities``: under ``unittest discover -s tests/concorde``, discovery itself imports
``tests/concorde/development/__init__.py`` as top-level module ``capabilities`` while walking the
tree, which would otherwise permanently shadow the real repository-root package for this process.
"""
from __future__ import annotations

import importlib
import sys
import unittest

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.spec.contracts import (  # noqa: E402
    COMPOSITE_CAPABILITIES,
    GLOBAL_CAPABILITIES,
    STAGE_CAPABILITIES,
    LIFECYCLE_CAPABILITIES,
    MAIN_ROUTED_CAPABILITIES,
    CAPABILITY_NAMES,
    SKILL_NAMES,
    dependencies,
    load_capability_inventory,
    schemas,
)

capabilities = load_capability_inventory()


def _modules():
    return {name: importlib.import_module(f"{capabilities.__name__}.{name}") for name in capabilities.CAPABILITIES}


class CapabilityModuleContractTests(unittest.TestCase):
    def test_capability_names_match_the_capability_registry_exactly(self):
        external_names = {capabilities.external_name(name) for name in capabilities.CAPABILITIES}
        self.assertEqual(external_names, set(CAPABILITY_NAMES))
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
            if external in GLOBAL_CAPABILITIES:
                self.assertEqual(module.CLASS, "global", external)
            elif external in LIFECYCLE_CAPABILITIES:
                self.assertEqual(module.CLASS, "lifecycle", external)
            elif external in STAGE_CAPABILITIES:
                self.assertEqual(module.CLASS, "stage", external)
            else:
                self.fail(f"{external} is not classified by any known capability partition")
        self.assertEqual(
            {name for name, module in modules.items() if module.CLASS == "global"},
            {name for name in capabilities.CAPABILITIES if capabilities.external_name(name) in GLOBAL_CAPABILITIES},
        )

    def test_agents_and_uses_match_dependencies_exactly(self):
        # dependencies() is the deterministic policy source, historically a flattened mix of Agent
        # identities and (for a composing capability) the external names of the capabilities it
        # composes. A module's own declared (AGENTS, USES) must reconstruct it exactly: the Agents
        # it launches itself, plus the external name of every capability it USES, plus (for a
        # main-routed capability other than main itself) the coordinator Agent main already grants.
        modules = _modules()
        for name, module in modules.items():
            external = module.EXTERNAL_NAME
            declared_agents = {"concorde-" + agent.name.replace("_", "-") for agent in module.AGENTS}
            used_names = {capabilities.external_name(used) for used in module.USES}
            expected = declared_agents | used_names
            if external in MAIN_ROUTED_CAPABILITIES and external != "concorde-main":
                expected = expected | {"concorde-coordinator"}
            self.assertEqual(set(dependencies(external)), expected, f"{external}: (AGENTS, USES) do not reconstruct dependencies()")

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
            set(COMPOSITE_CAPABILITIES),
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
        # (capability_service is imported lazily inside run()); importing every module and calling
        # its run() attribute (without invoking it) exercises that this loads cleanly.
        for name in capabilities.CAPABILITIES:
            module = importlib.import_module(f"{capabilities.__name__}.{name}")
            self.assertTrue(callable(module.run))

    def test_main_routed_capabilities_match_the_global_class(self):
        self.assertEqual(set(MAIN_ROUTED_CAPABILITIES), {"concorde-main", "concorde-dev-loop", "concorde-review"})
        self.assertTrue(set(MAIN_ROUTED_CAPABILITIES).issubset(GLOBAL_CAPABILITIES))

    def test_every_public_capability_class_is_global_or_lifecycle(self):
        modules = _modules()
        for name, module in modules.items():
            if module.EXTERNAL_NAME in SKILL_NAMES:
                self.assertIn(module.CLASS, {"global", "lifecycle"}, module.EXTERNAL_NAME)
            else:
                self.assertEqual(module.CLASS, "stage", module.EXTERNAL_NAME)


class InProcessCompositionTests(unittest.TestCase):
    """Every in-process nested dispatch the host can perform must match the declared USES graph.

    ``resolve_child_capability`` is the one place the host resolves a nested capability call
    (``Invocation.loop``'s stage graph, ``reflections_triage``'s composition of ``dev_loop``, and a
    Domain's own recursive per-component review routing). This exhaustively compares its behavior,
    for every ordered pair of capabilities, against each capability module's own declared ``USES``:
    self-recursion (fan-out across component targets, never a composition edge) always resolves;
    every other pair resolves if and only if the child is declared.
    """

    def test_resolution_exactly_matches_the_declared_uses_graph(self):
        from concorde.development.capability_host import resolve_child_capability
        from concorde.spec.repository import SpecError

        modules = _modules()
        externals = {name: module.EXTERNAL_NAME for name, module in modules.items()}
        for parent_name, parent_module in modules.items():
            declared = {externals[used] for used in parent_module.USES}
            for child_name, child_external in externals.items():
                parent_external = externals[parent_name]
                should_resolve = child_name == parent_name or child_external in declared
                if should_resolve:
                    resolved = resolve_child_capability(parent_external, child_external)
                    self.assertIs(resolved, modules[child_name], (parent_external, child_external))
                else:
                    with self.assertRaises(SpecError, msg=(parent_external, child_external)) as failure:
                        resolve_child_capability(parent_external, child_external)
                    self.assertEqual(failure.exception.code, "undeclared_capability")

    def test_undeclared_child_is_refused_with_the_stable_error_code(self):
        from concorde.development.capability_host import resolve_child_capability
        from concorde.spec.repository import SpecError

        with self.assertRaises(SpecError) as failure:
            resolve_child_capability("concorde-specify", "concorde-plan")
        self.assertEqual(failure.exception.code, "undeclared_capability")

    def test_declared_dev_loop_and_reflections_triage_edges_resolve(self):
        from concorde.development.capability_host import resolve_child_capability

        modules = _modules()
        for child in ("specify", "review", "plan", "tasks", "implement", "validate"):
            resolved = resolve_child_capability("concorde-dev-loop", modules[child].EXTERNAL_NAME)
            self.assertIs(resolved, modules[child])
        resolved = resolve_child_capability("concorde-reflections-triage", "concorde-dev-loop")
        self.assertIs(resolved, modules["dev_loop"])

    def test_self_recursion_never_requires_a_declared_edge(self):
        from concorde.development.capability_host import resolve_child_capability

        modules = _modules()
        for name, module in modules.items():
            resolved = resolve_child_capability(module.EXTERNAL_NAME, module.EXTERNAL_NAME)
            self.assertIs(resolved, module)


if __name__ == "__main__":
    unittest.main()
