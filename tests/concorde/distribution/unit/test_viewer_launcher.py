"""Exercise the documented viewer boundary without opening a browser or installing packages."""
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location("concorde_viewer_launcher", PACKAGE / "scripts/run-viewer.py")
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)


class ViewerLauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        manifest = json.loads((PACKAGE / "concorde.json").read_text())
        self.config = copy.deepcopy(manifest["viewer"])
        self.put(".concorde/framework/concorde.json", {"runtime": manifest["runtime"], "viewer": self.config})
        runtime = Path(".concorde/.venv")
        self.marker = str(runtime / ".concorde-runtime.json")
        self.put(self.marker, {"schema_version": 2, "owner": "concorde",
            "viewer_version": self.config["version"], "viewer_entrypoint": self.config["entrypoint"]})
        self.viewer_root = runtime / self.config["install_relative"]
        self.put(str(self.viewer_root / "node_modules" / self.config["package"] / "package.json"),
                 {"name": self.config["package"], "version": self.config["version"]})
        self.entrypoint = self.root / self.viewer_root / self.config["entrypoint"]
        self.entrypoint.parent.mkdir(parents=True, exist_ok=True)
        self.entrypoint.write_text("// Explicit subprocess test double; no viewer code runs.\n")
        self.graph = {"version": "1", "project": {"name": "Example"}, "nodes": [], "edges": []}
        self.put(".ua/knowledge-graph.json", self.graph)

    def put(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def launch(self, *flags):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return viewer.main(["--project-root", str(self.root), *flags])

    def test_launch_forwards_project_port_and_browser_choice_and_returns_child_status(self):
        with patch.object(viewer.shutil, "which", return_value="/test/node"), patch.object(viewer.subprocess, "run") as run:
            run.side_effect = [subprocess.CompletedProcess([], 0, "v22.1.0\n", ""),
                               subprocess.CompletedProcess([], 7)]
            self.assertEqual(7, self.launch("--port", "0", "--no-open"))
            self.assertEqual(2, run.call_count)
            self.assertEqual(["/test/node", str(self.entrypoint), str(self.root), "--port", "0", "--no-open"],
                             run.call_args.args[0])
            self.assertEqual(self.root, run.call_args.kwargs["cwd"])

    def test_first_existing_graph_is_selected_and_invalid_input_does_not_fall_back(self):
        first = self.config["graph_paths"][0]
        self.put(first, self.graph)
        self.assertEqual(self.root / first, viewer._raw_graph(self.root, self.config))
        self.put(first, {"tool": "explore", "result": {}})
        with self.assertRaisesRegex(viewer.ViewerLaunchError, "not Viewer input"):
            viewer._raw_graph(self.root, self.config)

    def test_stale_runtime_fails_before_any_process_starts(self):
        marker = json.loads((self.root / self.marker).read_text())
        marker["viewer_version"] = "0.0.0"
        self.put(self.marker, marker)
        with patch.object(viewer.subprocess, "run") as run:
            self.assertEqual(3, self.launch())
            run.assert_not_called()

    def test_missing_graph_or_symlink_is_rejected(self):
        graph = self.root / ".ua/knowledge-graph.json"
        graph.unlink()
        with self.assertRaisesRegex(viewer.ViewerLaunchError, "no raw Understand Anything graph"):
            viewer._raw_graph(self.root, self.config)
        self.put("graph.json", self.graph)
        graph.symlink_to(self.root / "graph.json")
        with self.assertRaisesRegex(viewer.ViewerLaunchError, "symlink"):
            viewer._raw_graph(self.root, self.config)

    def test_unsupported_node_and_invalid_ports_fail_without_viewer_execution(self):
        with patch.object(viewer.shutil, "which", return_value="/test/node"), patch.object(viewer.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "v16.0.0\n", "")
            self.assertEqual(3, self.launch())
            self.assertEqual(1, run.call_count)
        for port in ("-1", "65536", "invalid"):
            with self.subTest(port=port), self.assertRaises(SystemExit) as failed:
                self.launch("--port", port)
            self.assertEqual(2, failed.exception.code)


if __name__ == "__main__":
    unittest.main()
