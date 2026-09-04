from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.planning_context import (  # noqa: E402
    PlanningContextError,
    resolve_planning_context,
)
from concorde.understanding.feature_workspace import workspace_role_paths as resolve_workspace_roles  # noqa: E402


FIXTURE = REPOSITORY_ROOT / "tests/concorde/fixtures/permission-planning-project"
SELECTED = "specs/example/modules/consumer/features/001-change.md"


class PlanningContextTests(unittest.TestCase):
    def test_required_interface_owner_is_included_with_reason_and_incidental_relation_is_not(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        self.assertEqual(context.feature_path, SELECTED)
        self.assertEqual(
            [(item.feature_path, item.interface_ids) for item in context.required_feature_specs],
            [("specs/example/modules/provider/features/001-api.md", ("contract.provider.api",))],
        )
        readable = set(path for paths in context.role_paths.values() for path in paths)
        self.assertIn("specs/example/modules/provider/features/001-api.md", readable)
        self.assertNotIn("specs/example/modules/provider/features/002-unrelated.md", readable)

    def test_explicit_external_required_interface_needs_no_provider_feature(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            selected = project / SELECTED
            body = selected.read_text(encoding="utf-8").replace(
                "    - contract.provider.api\n",
                "    - contract.provider.api\n    - contract.external.platform\n",
            )
            external = """

### `contract.external.platform` — External platform

- **Provider**: external:fixture-platform
- **Consumer**: Consumer module
- **Direction**: Platform input to consumer behavior.
- **Entry points**: External platform workflow.
- **Inputs**: One platform request.
- **Outputs**: One platform result.
- **Obligations**: Surface provider unavailability.
- **Failures**: An unavailable platform stops the change.
- **Compatibility**: The external provider owns its versions.
"""
            selected.write_text(
                body.replace("\n## Usage Scenarios", external + "\n## Usage Scenarios"),
                encoding="utf-8",
            )

            context = resolve_planning_context(project, SELECTED)

            self.assertEqual(
                [(item.feature_path, item.interface_ids) for item in context.required_feature_specs],
                [("specs/example/modules/provider/features/001-api.md", ("contract.provider.api",))],
            )

    def test_required_interface_without_project_or_external_provider_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            selected = project / SELECTED
            selected.write_text(
                selected.read_text(encoding="utf-8").replace(
                    "    - contract.provider.api\n",
                    "    - contract.missing.api\n",
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                PlanningContextError,
                "required interface 'contract.missing.api' has 0 provider owners",
            ):
                resolve_planning_context(project, SELECTED)

    def test_selected_module_owned_locators_and_task_paths_are_bounded(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        self.assertEqual(
            context.owned_implementation_paths,
            ("src/consumer/service.py", "tests/consumer/test_service.py"),
        )
        self.assertEqual(context.task_authorized_paths, context.owned_implementation_paths)
        self.assertEqual(
            context.role_paths["owned-implementation"],
            context.owned_implementation_paths,
        )
        self.assertRegex(context.source_digest, r"^sha256:[0-9a-f]{64}$")

    def test_provider_internals_other_attempts_and_undeclared_paths_are_denied(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        denied = set(context.denied_paths)
        self.assertTrue(
            {
                "specs/example/modules/provider/architecture.md",
                "src/provider/private.py",
                "tests/provider/test_private.py",
                ".concorde/attempts/feature.example.other",
            }.issubset(denied)
        )
        readable = set(path for paths in context.role_paths.values() for path in paths)
        self.assertTrue(denied.isdisjoint(readable))

    def test_provider_private_paths_override_exact_parent_owned_locators(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            root_feature = "specs/example/features/001-root.md"
            architecture = project / "specs/example/architecture.md"
            architecture.write_text(
                architecture.read_text(encoding="utf-8")
                .replace("features: []", "features:\n  - feature.example.root")
                .replace(
                    "| `module.example.provider` | module | Provider boundary. | `specs/example/modules/provider/architecture.md` |",
                    "| `module.example.provider` | module | Provider boundary. | `specs/example/modules/provider/architecture.md` |\n"
                    "| `entity.example.private-locator` | program | A parent-owned locator that names provider internals. | `src/provider/private.py` |",
                ),
                encoding="utf-8",
            )
            (project / root_feature).parent.mkdir(parents=True, exist_ok=True)
            (project / root_feature).write_text(
                """---
id: feature.example.root
kind: feature
module: module.example
related_features: []
interfaces:
  provided:
    - contract.example.root
  required:
    - contract.provider.api
---

# Feature Design: Root Change

## Outcome and Scope

The root changes through the provider's published API.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.example.private-locator` | Parent-owned locator that collides with provider internals. |

## Interfaces

### `contract.example.root` — Change the root

- **Consumer**: Fixture maintainer
- **Direction**: Request to root result.
- **Entry points**: `entity.example.private-locator`
- **Inputs**: A bounded change request.
- **Outputs**: Updated root behavior.
- **Obligations**: Use only the published provider contract.
- **Failures**: Missing provider behavior stops the change.
- **Compatibility**: Stable fixture identity.
- **Implementing entities**: `entity.example.private-locator`

## Usage Scenarios

1. The maintainer changes the root through `contract.provider.api`.

## Requirements

- **FR-001**: Planning includes the provider feature that owns `contract.provider.api`.

## Edge Cases

- A parent-owned locator that names provider internals stays denied.
""",
                encoding="utf-8",
            )

            def roles_without_current_attempt_tasks(project_root, workspace):
                return {**resolve_workspace_roles(project_root, workspace), "task-authorized": ()}

            with mock.patch(
                "concorde.understanding.planning_context.workspace_role_paths",
                side_effect=roles_without_current_attempt_tasks,
            ):
                context = resolve_planning_context(project, root_feature)
            required = {item.feature_id: item.feature_path for item in context.required_feature_specs}
            self.assertEqual(
                required,
                {"feature.example.provider.api": "specs/example/modules/provider/features/001-api.md"},
            )
            overlaps = {"src/provider/private.py", "specs/example/modules/provider/architecture.md"}
            self.assertTrue(overlaps.issubset(context.denied_paths))
            self.assertTrue(overlaps.isdisjoint(context.owned_implementation_paths))
            self.assertIn("specs/example/modules/consumer/architecture.md", context.owned_implementation_paths)
            readable = {path for paths in context.role_paths.values() for path in paths}
            self.assertTrue(readable.isdisjoint(context.denied_paths))

    def test_same_module_and_ancestor_providers_are_not_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            consumer = project / "specs/example/modules/consumer"
            architecture = consumer / "architecture.md"
            architecture.write_text(
                architecture.read_text(encoding="utf-8").replace(
                    "  - feature.example.consumer.change\n",
                    "  - feature.example.consumer.change\n  - feature.example.consumer.helper\n",
                ),
                encoding="utf-8",
            )
            (consumer / "features/002-helper.md").write_text(
                """---
id: feature.example.consumer.helper
kind: feature
module: module.example.consumer
related_features: []
interfaces:
  provided:
    - contract.consumer.helper
  required: []
---

# Feature Design: Consumer Helper

## Outcome and Scope

A sibling feature in the same module publishes a helper contract.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.example.consumer-service` | Hosts the helper. |

## Interfaces

### `contract.consumer.helper` — Consumer helper

- **Consumer**: Sibling consumer features
- **Direction**: Request to helper result.
- **Entry points**: `entity.example.consumer-service`
- **Inputs**: A helper request.
- **Outputs**: A helper result.
- **Obligations**: Stay inside the consumer module.
- **Failures**: A missing helper stops the caller.
- **Compatibility**: Stable fixture identity.
- **Implementing entities**: `entity.example.consumer-service`

## Usage Scenarios

1. The change feature calls the helper.

## Requirements

- **FR-001**: The helper is published inside the consumer module.

## Edge Cases

- None.
""",
                encoding="utf-8",
            )
            selected = project / SELECTED
            selected.write_text(
                selected.read_text(encoding="utf-8").replace(
                    "    - contract.provider.api\n",
                    "    - contract.provider.api\n    - contract.consumer.helper\n",
                ),
                encoding="utf-8",
            )

            context = resolve_planning_context(project, SELECTED)

            required = {item.feature_id: item.feature_path for item in context.required_feature_specs}
            self.assertEqual(
                required,
                {
                    "feature.example.provider.api": "specs/example/modules/provider/features/001-api.md",
                    "feature.example.consumer.helper": "specs/example/modules/consumer/features/002-helper.md",
                },
            )
            self.assertNotIn("specs/example/modules/consumer/architecture.md", context.denied_paths)
            self.assertIn("specs/example/modules/provider/architecture.md", context.denied_paths)
            self.assertEqual(
                context.owned_implementation_paths,
                ("src/consumer/service.py", "tests/consumer/test_service.py"),
            )
            readable = {path for paths in context.role_paths.values() for path in paths}
            self.assertTrue(readable.isdisjoint(context.denied_paths))

    def test_path_escapes_symlinks_and_cross_module_task_writes_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            owned = project / "src/consumer/service.py"
            target = project / "src/provider/private.py"
            owned.unlink()
            owned.symlink_to(target)
            with self.assertRaisesRegex(PlanningContextError, "symlink"):
                resolve_planning_context(project, SELECTED)

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            tasks = project / ".concorde/attempts/feature.example.consumer.change/tasks.md"
            tasks.write_text(
                tasks.read_text() + "- [ ] T002 Edit `src/provider/private.py` [FR-002]\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PlanningContextError, "outside providing module"):
                resolve_planning_context(project, SELECTED)


if __name__ == "__main__":
    unittest.main()
