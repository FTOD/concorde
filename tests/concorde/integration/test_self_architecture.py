import json
import subprocess
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False)


def repository_evidence_diagrams():
    """Every maintained diagram under specs/ that declares Archify repository evidence."""
    for diagram_path in sorted((REPOSITORY_ROOT / "specs").rglob("diagrams/*.json")):
        diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
        repository = (diagram.get("meta") or {}).get("repository")
        if repository:
            yield diagram_path.relative_to(REPOSITORY_ROOT).as_posix(), diagram, repository


class SelfArchitectureTests(unittest.TestCase):
    def test_concorde_hierarchy_validates_and_projects_one_level(self):
        validation = validate_project(REPOSITORY_ROOT)
        self.assertEqual(validation.status, "success", validation.findings)
        context = bounded_context(REPOSITORY_ROOT, "module.concorde")
        self.assertEqual(context.status, "success", context.findings)
        projection = context.result["context"]
        self.assertEqual(len(projection["children"]), 5)
        self.assertTrue(all("contracts" in child for child in projection["children"]))
        participants = {
            participant
            for scenario in projection["scenarios"]
            for participant in scenario["participants"]
        }
        self.assertTrue(
            {
                "module.concorde.skills",
                "module.concorde.scripts",
                "module.concorde.workspace-files",
                "module.concorde.distribution",
                "module.concorde.auto-docs",
            }.issubset(participants)
        )
        self.assertFalse(any(participant.startswith("feature.") for participant in participants))
        self.assertNotIn("feature.auto-docs.publish-project-docsite", repr(projection["children"]))
        refinements = {(item["from"], item["to"]) for item in projection["refinement_links"]}
        self.assertIn(("feature.distribution.package-concorde-bundle", "feature.concorde.install-with-spec-kit"), refinements)
        self.assertIn(("feature.scripts.run-workflow-operations", "feature.concorde.workflow"), refinements)
        self.assertIn(("feature.workspace-files.manage-feature-workspace", "feature.concorde.workflow"), refinements)

    def test_workflow_diagram_cites_maintained_preset_sources_for_preset_owned_surfaces(self):
        diagram = json.loads((
            REPOSITORY_ROOT
            / "specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json"
        ).read_text(encoding="utf-8"))
        components = {item["id"]: item for item in diagram["components"]}
        materialized_roots = (".agents/", ".claude/", ".specify/")
        for component_id in ("phaseCommands", "fastLoop"):
            component = components[component_id]
            self.assertEqual(component["tag"], "preset · modifies")
            cited = [source["path"] for source in component["sources"]]
            self.assertTrue(
                any(path.startswith("presets/concorde/") for path in cited),
                f"{component_id} must cite the maintained preset, cited: {cited}",
            )
            self.assertEqual(
                [path for path in cited if path.startswith(materialized_roots)], [],
                f"{component_id} cites a materialization instead of the preset: {cited}",
            )
        self.assertIn(
            "presets/concorde/commands/speckit.fast-loop.md",
            [source["path"] for source in components["fastLoop"]["sources"]],
        )
        for component in diagram["components"]:
            for source in component.get("sources") or []:
                self.assertTrue(
                    (REPOSITORY_ROOT / source["path"]).is_file(),
                    f"component {component['id']!r} cites {source['path']}, which is not in the checkout",
                )

    def test_question_surface_is_visible_but_not_a_runtime_operation(self):
        manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(encoding="utf-8")
        command_names = [
            line.split('"', 2)[1]
            for line in manifest.splitlines()
            if line.strip().startswith('- name: "speckit.concorde.')
        ]
        self.assertEqual(len(command_names), 5)
        self.assertIn("speckit.concorde.ask", command_names)

        diagram = json.loads((
            REPOSITORY_ROOT
            / "specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json"
        ).read_text(encoding="utf-8"))
        command_component = next(item for item in diagram["components"] if item["id"] == "concordeCommands")
        self.assertIn("5 Concorde Surfaces", command_component["label"])
        self.assertIn("4 operations", command_component["sublabel"])

        cli_source = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/cli.py").read_text(encoding="utf-8")
        self.assertNotIn('add_parser("ask")', cli_source)

    def test_repository_evidence_diagrams_resolve_in_checkout_and_at_pinned_revision(self):
        checked = 0
        for relative, diagram, repository in repository_evidence_diagrams():
            revision = str(repository.get("revision", ""))
            self.assertRegex(
                revision, r"^[0-9a-f]{40}$",
                f"{relative}: meta.repository.revision must be a full 40-character commit SHA",
            )
            self.assertEqual(
                _git("cat-file", "-e", f"{revision}^{{commit}}").returncode, 0,
                f"{relative}: pinned revision {revision} is not in this repository's history",
            )
            for component in diagram.get("components", []):
                for source in component.get("sources") or []:
                    path = source["path"]
                    where = f"{relative}: component {component['id']!r} cites {path}"
                    self.assertTrue(
                        (REPOSITORY_ROOT / path).is_file(),
                        f"{where}, which no longer exists in the checkout; cite the migrated path",
                    )
                    self.assertEqual(
                        _git("cat-file", "-t", f"{revision}:{path}").stdout.strip(), "blob",
                        f"{where}, which does not exist at pinned revision {revision[:7]}; commit the "
                        "path change first, then pin that commit in meta.repository.revision",
                    )
                    checked += 1
        self.assertGreater(checked, 0, "no repository-evidence diagram was found under specs/")

    def test_self_hosting_diagram_cites_authoritative_framework_sources(self):
        diagram = json.loads((
            REPOSITORY_ROOT
            / "specs/concorde/features/004-self-host-concorde/diagrams/concorde-self-hosting-components.json"
        ).read_text(encoding="utf-8"))
        component = next(item for item in diagram["components"] if item["id"] == "frameworkSources")
        cited = [source["path"] for source in component["sources"]]
        self.assertIn("presets/concorde/preset.yml", cited)
        self.assertIn("extensions/concorde/extension.yml", cited)
        materialized_roots = (".agents/", ".claude/", ".specify/")
        self.assertEqual([path for path in cited if path.startswith(materialized_roots)], [], cited)


if __name__ == "__main__":
    unittest.main()
