"""Deterministic UA graph export: skeleton, overlay, shared files, --check and invalid input."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.cli import main  # noqa: E402
from concorde.spec.initialize import apply_project_proposal, project_proposal  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402
from concorde.views.ua_graph import export_ua_graph  # noqa: E402
from tests.concorde.spec.support import CONFIGURATION, block, module_document  # noqa: E402


ROOT_DOC = module_document(
    "document.root", "module.root", "Root",
    "Root composes Alpha and Beta for the ua-graph export fixture.",
    "### scenario.root.compose — Root is only a composition\n\n"
    "- GIVEN the registered project\n"
    "- WHEN Root is read\n"
    "- THEN it names Alpha and Beta as its children\n",
    ("Root owns no implementation of its own; each entity stands for one child Module.",
     [{"id": "entity.root.alpha", "title": "Alpha", "kind": "module",
       "responsibility": "Owns the core and pending implementation.", "target_id": "module.alpha"},
      {"id": "entity.root.beta", "title": "Beta", "kind": "module",
       "responsibility": "Owns the service implementation.", "target_id": "module.beta"}]),
    "Root only composes its two children; it binds no files of its own.",
    "flowchart TB\n"
    "    accTitle: Root composition\n"
    "    accDescr: Root composes Alpha and Beta.\n"
    "    alpha[\"Alpha\"]\n    beta[\"Beta\"]\n"
    "    alpha -->|coordinates with| beta",
)

ALPHA_DEPENDENCIES = [{
    "target_id": "module.beta",
    "responsibility": "Supplies the beta service that alpha reads through.",
    "selection_condition": "Select when alpha needs the beta service.",
    "relied_upon_promises": ["scenario.beta.serve: beta answers every request it receives."],
}]

ALPHA_DOC = module_document(
    "document.alpha", "module.alpha", "Alpha",
    "Alpha owns its core calculation, a pending feature, and shares one utility file with Beta.",
    "### scenario.alpha.core — Alpha computes its own result\n\n"
    "- GIVEN Alpha's registered core file\n"
    "- WHEN Alpha runs\n"
    "- THEN it uses the shared utility and the beta service\n",
    ("Alpha's own files are the core and pending feature; the shared utility is realized jointly with Beta.",
     [{"id": "entity.alpha.core", "title": "Core", "kind": "program",
       "responsibility": "Alpha's own calculation.", "files": ["src/alpha/core.py"]},
      {"id": "entity.alpha.pending", "title": "Pending feature", "kind": "program",
       "responsibility": "A declared feature not yet delivered.",
       "files": ["src/alpha/pending_feature.py"], "pending": ["src/alpha/pending_feature.py"]},
      {"id": "entity.alpha.shared", "title": "Shared utility", "kind": "shared program",
       "responsibility": "One utility file realized jointly with Beta.", "files": ["src/shared/util.py"]},
      {"id": "entity.alpha.beta", "title": "Beta", "kind": "used module",
       "responsibility": "Supplies the beta service.", "target_id": "module.beta"}]),
    "The core and the pending feature both read the shared utility; Alpha also depends on Beta.",
    "flowchart TB\n"
    "    accTitle: Alpha implementation\n"
    "    accDescr: Alpha's core and pending feature read the shared utility, and Alpha depends on Beta.\n"
    "    core[\"Core\"]\n    pending[\"Pending feature\"]\n    shared[\"Shared utility\"]\n    beta[\"Beta\"]\n"
    "    core -->|reads| shared\n"
    "    pending -->|will read| shared\n"
    "    core -->|depends on| beta",
    ALPHA_DEPENDENCIES,
)

BETA_DOC = module_document(
    "document.beta", "module.beta", "Beta",
    "Beta serves requests through its own service and shares one utility file with Alpha.",
    "### scenario.beta.serve — Beta answers every request it receives\n\n"
    "- GIVEN Beta's registered service file\n"
    "- WHEN a request arrives\n"
    "- THEN Beta answers using the shared utility\n",
    ("Beta's own file is the service; the shared utility is realized jointly with Alpha.",
     [{"id": "entity.beta.service", "title": "Service", "kind": "program",
       "responsibility": "Beta's own request handling.", "files": ["src/beta/service.py"]},
      {"id": "entity.beta.shared", "title": "Shared utility", "kind": "shared program",
       "responsibility": "One utility file realized jointly with Alpha.", "files": ["src/shared/util.py"]}]),
    "The service reads the shared utility.",
    "flowchart TB\n"
    "    accTitle: Beta implementation\n"
    "    accDescr: Beta's service reads the shared utility.\n"
    "    service[\"Service\"]\n    shared[\"Shared utility\"]\n"
    "    service -->|reads| shared",
)


def _target(target_id, title, documents, *, parent=None, uses=(), files=()):
    return {"id": target_id, "kind": "module", "title": title, "documents": documents,
            "parent": parent, "uses": list(uses), "files": sorted(files), "checks": []}


def build_project(root: Path) -> None:
    """A minimal registered project: Root composes Alpha and Beta; Alpha uses Beta; they share
    ``src/shared/util.py``; Alpha additionally declares one pending file that already exists."""
    apply_project_proposal(root, REPOSITORY_ROOT,
                           project_proposal(root, REPOSITORY_ROOT, "Fixture", CONFIGURATION, "module.root"))
    targets = [
        _target("module.root", "Root", ["specs/root/module.md"]),
        _target("module.alpha", "Alpha", ["specs/alpha/module.md"], parent="module.root", uses=["module.beta"],
                files=["src/alpha/core.py", "src/alpha/pending_feature.py", "src/shared/util.py"]),
        _target("module.beta", "Beta", ["specs/beta/module.md"], parent="module.root",
                files=["src/beta/service.py", "src/shared/util.py"]),
    ]
    registry = {"schema_version": 3, "project_id": "project.fixture", "entry_target": "module.root",
                "targets": targets, "checks": []}
    (root / ".concorde/specs.json").write_text(json.dumps(registry))
    files = {
        "specs/root/module.md": ROOT_DOC,
        "specs/alpha/module.md": ALPHA_DOC,
        "specs/beta/module.md": BETA_DOC,
        "src/alpha/core.py": "# core\n",
        "src/alpha/pending_feature.py": "# pending, created but not yet delivered\n",
        "src/shared/util.py": "# shared utility\n",
        "src/beta/service.py": "# service\n",
    }
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def node(graph, node_id):
    return next(item for item in graph["nodes"] if item["id"] == node_id)


def edges(graph, source=None, target=None, kind=None):
    return [e for e in graph["edges"] if (source is None or e["source"] == source)
            and (target is None or e["target"] == target) and (kind is None or e["type"] == kind)]


def layer(graph, layer_id):
    return next((item for item in graph["layers"] if item["id"] == layer_id), None)


class UaGraphSkeletonTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)

    def load(self):
        return json.loads((self.root / ".ua/knowledge-graph.json").read_text(encoding="utf-8"))

    @verifies("scenario.views.ua-graph-skeleton")
    def test_skeleton_export_derives_only_from_the_registry(self):
        result = export_ua_graph(self.root)
        self.assertEqual("success", result.status, result.findings)
        self.assertEqual((".ua/knowledge-graph.json",), result.artifacts)
        graph = self.load()
        self.assertEqual("1.0.0", graph["version"])
        self.assertEqual("project.fixture", graph["project"]["name"])
        self.assertEqual([], graph["project"]["languages"])
        self.assertEqual([], graph["tour"])

        root_module = node(graph, "module:module.root")
        self.assertEqual("Root", root_module["name"])
        self.assertEqual("Root composes Alpha and Beta for the ua-graph export fixture.", root_module["summary"])
        self.assertIn("concorde-ua-graph", root_module["tags"])

        self.assertEqual(1, len(edges(graph, "module:module.root", "module:module.alpha", "contains")))
        self.assertEqual(1, len(edges(graph, "module:module.root", "module:module.beta", "contains")))
        depends = edges(graph, "module:module.alpha", "module:module.beta", "depends_on")
        self.assertEqual(1, len(depends))
        self.assertEqual("Supplies the beta service that alpha reads through.", depends[0]["description"])

        core_edges = edges(graph, "module:module.alpha", kind="contains")
        core_target_ids = {e["target"] for e in core_edges}
        self.assertIn("file:src/alpha/core.py", core_target_ids)
        self.assertIn("file:src/alpha/pending_feature.py", core_target_ids)
        pending_node = node(graph, "file:src/alpha/pending_feature.py")
        self.assertIn("pending", pending_node["tags"])
        core_node = node(graph, "file:src/alpha/core.py")
        self.assertNotIn("pending", core_node["tags"])

        # Root binds no files, so it gets no layer; Alpha and Beta each get exactly one.
        self.assertIsNone(layer(graph, "layer:module.root"))
        self.assertIsNotNone(layer(graph, "layer:module.alpha"))
        self.assertIsNotNone(layer(graph, "layer:module.beta"))
        self.assertIsNone(layer(graph, "layer:unlisted"))

        doc_node = node(graph, "document:specs/alpha/module.md")
        self.assertEqual("document.alpha", doc_node["summary"])
        self.assertEqual(1, len(edges(graph, "document:specs/alpha/module.md", "module:module.alpha", "documents")))


class UaGraphOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)
        self.ua_path = self.root / ".ua/knowledge-graph.json"
        self.ua_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_graph = {
            "version": "2.7.1",
            "project": {"name": "external-scan", "languages": ["python"], "frameworks": [],
                        "description": "A prior scan performed by the real Understand Anything tool.",
                        "analyzedAt": "2026-01-01T00:00:00Z", "gitCommitHash": "abc123"},
            "nodes": [
                {"id": "file:99", "type": "file", "name": "core.py", "filePath": "src/alpha/core.py",
                 "summary": "Original UA summary of core.py.", "tags": ["source"]},
                {"id": "class:99:Core", "type": "class", "name": "Core", "filePath": "src/alpha/core.py",
                 "summary": "A class UA found inside core.py.", "tags": ["source"]},
                {"id": "config:42", "type": "config", "name": "pyproject.toml", "filePath": "pyproject.toml",
                 "summary": "A config file no Module lists.", "tags": ["source"]},
                {"id": "file:77", "type": "file", "name": "settings.py", "filePath": "unrelated/settings.py",
                 "summary": "A real scan's own file, whose organic tags happen to include the project's name.",
                 "tags": ["source", "concorde"]},
            ],
            "edges": [
                {"source": "file:99", "target": "class:99:Core", "type": "contains",
                 "direction": "forward", "weight": 1.0},
            ],
            "layers": [
                {"id": "layer:hand-authored", "name": "Hand-authored layer",
                 "description": "A layer a human curated, unrelated to any Module.", "nodeIds": ["file:99"]},
            ],
            "tour": [{"order": 1, "title": "Start here", "description": "Tour step from the real tool."}],
        }
        self.ua_path.write_text(json.dumps(self.base_graph))

    def load(self):
        return json.loads(self.ua_path.read_text(encoding="utf-8"))

    @verifies("scenario.views.ua-graph-overlay")
    def test_overlay_reuses_existing_nodes_and_preserves_foreign_data(self):
        result = export_ua_graph(self.root)
        self.assertEqual("success", result.status, result.findings)
        graph = self.load()

        # Non-Concorde project/version/tour and hand-authored layer/nodes/edges survive untouched.
        self.assertEqual(self.base_graph["version"], graph["version"])
        self.assertEqual(self.base_graph["project"], graph["project"])
        self.assertEqual(self.base_graph["tour"], graph["tour"])
        self.assertEqual(self.base_graph["nodes"][0], node(graph, "file:99"))
        self.assertEqual(self.base_graph["nodes"][1], node(graph, "class:99:Core"))
        # A real scan's own "concorde" tag (e.g. the literal project name) is not the exporter's
        # marker tag and must not cause this foreign node to be stripped.
        self.assertEqual(self.base_graph["nodes"][3], node(graph, "file:77"))
        self.assertEqual(1, len(edges(graph, "file:99", "class:99:Core", "contains")))
        self.assertIsNotNone(layer(graph, "layer:hand-authored"))

        # The pre-existing file:99 node (not file:src/alpha/core.py) is reused by filePath.
        alpha_contains = edges(graph, "module:module.alpha", kind="contains")
        core_edge = next(e for e in alpha_contains if e["target"] == "file:99")
        self.assertEqual("entity.alpha.core: Core", core_edge["description"])
        self.assertFalse(any(n["id"] == "file:src/alpha/core.py" for n in graph["nodes"]))

        # Module nodes are freshly added; the unlisted layer holds only file-like nodes (not the
        # "class" node) that no Module's entities bind.
        self.assertIsNotNone(node(graph, "module:module.alpha"))
        unlisted = layer(graph, "layer:unlisted")
        self.assertIsNotNone(unlisted)
        self.assertEqual(["config:42", "file:77"], unlisted["nodeIds"])
        self.assertIn("file:99", layer(graph, "layer:module.alpha")["nodeIds"])

    def test_overlay_export_is_idempotent(self):
        export_ua_graph(self.root)
        first = self.ua_path.read_bytes()
        export_ua_graph(self.root)
        second = self.ua_path.read_bytes()
        self.assertEqual(first, second)


class UaGraphSharedFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)

    @verifies("scenario.views.ua-graph-shared-file")
    def test_shared_file_belongs_to_the_first_lister_and_gets_a_related_edge(self):
        result = export_ua_graph(self.root)
        self.assertEqual("success", result.status, result.findings)
        graph = json.loads((self.root / ".ua/knowledge-graph.json").read_text(encoding="utf-8"))

        shared_id = "file:src/shared/util.py"
        self.assertEqual(1, len([n for n in graph["nodes"] if n["id"] == shared_id]))

        # Alpha is registered before Beta, so Alpha's layer claims the shared file.
        self.assertIn(shared_id, layer(graph, "layer:module.alpha")["nodeIds"])
        self.assertNotIn(shared_id, layer(graph, "layer:module.beta")["nodeIds"])

        # Both Modules still get their own "contains" edge from their own entity.
        alpha_edge = edges(graph, "module:module.alpha", shared_id, "contains")
        beta_edge = edges(graph, "module:module.beta", shared_id, "contains")
        self.assertEqual(1, len(alpha_edge))
        self.assertEqual(1, len(beta_edge))
        self.assertEqual("entity.alpha.shared: Shared utility", alpha_edge[0]["description"])
        self.assertEqual("entity.beta.shared: Shared utility", beta_edge[0]["description"])

        related = edges(graph, shared_id, "module:module.beta", "related")
        self.assertEqual(1, len(related))
        self.assertEqual("also listed by module.beta", related[0]["description"])
        self.assertEqual(0, len(edges(graph, shared_id, "module:module.alpha", "related")))


class UaGraphCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)
        self.ua_path = self.root / ".ua/knowledge-graph.json"

    @verifies("scenario.views.ua-graph-check")
    def test_check_passes_when_current_and_fails_when_stale(self):
        export_ua_graph(self.root)
        fresh_bytes = self.ua_path.read_bytes()

        result = export_ua_graph(self.root, check=True)
        self.assertEqual("success", result.status, result.findings)
        self.assertEqual(fresh_bytes, self.ua_path.read_bytes())

        registry_path = self.root / ".concorde/specs.json"
        registry = json.loads(registry_path.read_text())
        next(t for t in registry["targets"] if t["id"] == "module.alpha")["title"] = "Alpha Renamed"
        registry_path.write_text(json.dumps(registry))

        stale = export_ua_graph(self.root, check=True)
        self.assertEqual("invalid", stale.status)
        self.assertEqual({"CONCORDE-UA-GRAPH-003"}, {f.rule_id for f in stale.findings})
        self.assertEqual(fresh_bytes, self.ua_path.read_bytes())  # --check never writes

        refreshed = export_ua_graph(self.root)
        self.assertEqual("success", refreshed.status)
        graph = json.loads(self.ua_path.read_text(encoding="utf-8"))
        self.assertEqual("Alpha Renamed", node(graph, "module:module.alpha")["name"])


class UaGraphInvalidInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)
        self.ua_path = self.root / ".ua/knowledge-graph.json"
        self.ua_path.parent.mkdir(parents=True, exist_ok=True)

    @verifies("scenario.views.ua-graph-invalid-input")
    def test_malformed_existing_graph_is_rejected_without_writing(self):
        self.ua_path.write_text(json.dumps({"version": "1.0.0", "project": {}, "nodes": "not-a-list", "edges": []}))
        before = self.ua_path.read_bytes()

        result = export_ua_graph(self.root)
        self.assertEqual("invalid", result.status)
        self.assertEqual({"CONCORDE-UA-GRAPH-002"}, {f.rule_id for f in result.findings})
        self.assertEqual(before, self.ua_path.read_bytes())

        checked = export_ua_graph(self.root, check=True)
        self.assertEqual("invalid", checked.status)
        self.assertEqual({"CONCORDE-UA-GRAPH-002"}, {f.rule_id for f in checked.findings})
        self.assertEqual(before, self.ua_path.read_bytes())


class UaGraphCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_project(self.root)

    def test_cli_export_round_trip(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main(["--project-root", str(self.root), "ua-graph", "--allow-primary-worktree"])
        self.assertEqual(0, exit_code)
        payload = json.loads(buffer.getvalue())
        self.assertEqual("ua-graph", payload["tool"])
        self.assertEqual("success", payload["status"])
        self.assertTrue((self.root / ".ua/knowledge-graph.json").is_file())

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main(["--project-root", str(self.root), "ua-graph", "--check", "--allow-primary-worktree"])
        self.assertEqual(0, exit_code)
        self.assertEqual("success", json.loads(buffer.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
