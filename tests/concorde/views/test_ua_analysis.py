"""Whole-UA native-host bridge: real fake-host subprocesses, no model/network calls."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.cli import main
from concorde.spec.verification import verifies
from concorde.views.ua_analysis import analyze_ua
from tests.concorde.views.test_ua_graph import build_project

FAKE_HOST = r"""#!/usr/bin/env python3
import datetime, hashlib, json, os, pathlib, re, subprocess, sys, time
if '--version' in sys.argv:
    print('2.1.273 (Fake Claude test host)')
    sys.exit(0)
if '--help' in sys.argv:
    print('--settings --add-dir --append-system-prompt --max-budget-usd')
    sys.exit(0)
mode = os.environ.get('UA_FAKE_MODE', 'success')
if sys.argv[1:3] == ['auth', 'status']:
    print(json.dumps({'loggedIn': mode != 'unauthenticated'}))
    sys.exit(0)
prompt = sys.stdin.read()
if prompt.startswith('CONCORDE_UA_PERMISSION_PROBE'):
    run = pathlib.Path(json.loads(re.search(r'^Probe run directory: (.+)$', prompt, re.M).group(1)))
    nonce = re.search(r'^Probe nonce: (.+)$', prompt, re.M).group(1)
    (run / 'observed-probe.json').write_text(json.dumps({'argv': sys.argv[1:], 'prompt': prompt}))
    inputs = json.loads((run / 'input.json').read_text())
    scan = pathlib.Path(inputs['ua_directory']) / 'tmp/concorde-permission-scan.json'
    scan.write_text(json.dumps({'files': [{'path': 'src/alpha/core.py'}]}))
    report = json.dumps({'nonce': nonce, 'status': 'complete'})
    (run / 'probe-parent.json').write_text(report)
    if mode != 'probe-missing-child':
        (run / 'probe-child.json').write_text(report)
    print(json.dumps({'is_error': False, 'permission_denials': ['Bash'] if mode == 'probe-permission' else [], 'subagent_stats': {'spawned': 1}}))
    sys.exit(0)
run_input = pathlib.Path(json.loads(re.search(r'^Input manifest: (.+)$', prompt, re.M).group(1)))
run = run_input.parent
inputs = json.loads(run_input.read_text())
(run / 'observed.json').write_text(json.dumps({
    'argv': sys.argv[1:], 'redirect': os.environ.get('UNDERSTAND_NO_WORKTREE_REDIRECT'),
    'cwd': str(pathlib.Path.cwd()), 'prompt': prompt,
}))
mode = os.environ.get('UA_FAKE_MODE', 'success')
if mode == 'timeout':
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    (run / 'child.json').write_text(json.dumps({'pid': child.pid}))
    time.sleep(60)
if mode == 'error':
    print('native failure', file=sys.stderr)
    sys.exit(7)
ua = pathlib.Path(inputs['ua_directory'])
ua.mkdir(exist_ok=True)
graph = json.loads((run / 'seed.json').read_text())
graph['project']['description'] = 'Fake-host code analysis'
graph['nodes'][0]['summary'] = 'Enriched by native host'
graph['nodes'].append({'id': 'function:src/alpha/core.py:f', 'type': 'function',
    'name': 'f', 'summary': 'Function found in code', 'tags': ['code'], 'complexity': 'simple', 'filePath': 'src/alpha/core.py'})
graph['nodes'].append({'id': 'file:src/unbound.py', 'type': 'file', 'name': 'unbound.py',
    'summary': 'Unbound code is analyzed too', 'tags': ['code'], 'complexity': 'simple', 'filePath': 'src/unbound.py'})
graph['layers'][0]['nodeIds'].append('file:src/unbound.py')
graph['edges'].append({'source': 'file:src/alpha/core.py', 'target': 'function:src/alpha/core.py:f',
    'type': 'contains', 'weight': 1, 'direction': 'forward'})
graph['tour'] = [{'order': 1, 'title': 'Start', 'description': 'Read code', 'nodeIds': ['file:src/unbound.py']}]
if mode == 'missing-seed':
    graph['nodes'] = [n for n in graph['nodes'] if n['id'] != 'module:module.root']
    graph['edges'] = [e for e in graph['edges'] if 'module:module.root' not in (e['source'], e['target'])]
if mode == 'lost-relation':
    graph['edges'] = graph['edges'][1:]
if mode == 'dangling':
    graph['edges'][0]['target'] = 'absent'
if mode == 'bad-layer':
    graph['layers'][0]['nodeIds'].append('absent')
if mode == 'lost-code':
    graph['nodes'] = [n for n in graph['nodes'] if n.get('filePath') != 'src/unbound.py']
    graph['layers'][0]['nodeIds'].remove('file:src/unbound.py')
    graph['tour'] = []
if mode == 'mutate-code':
    pathlib.Path('src/unbound.py').write_text('# changed concurrently\n')
if mode == 'mutate-spec':
    with pathlib.Path('specs/alpha/module.md').open('a') as f:
        f.write('\nChanged during analysis.\n')
if mode == 'native-schema':
    graph['version'] = 123
if mode == 'duplicate-node':
    graph['nodes'].append(graph['nodes'][0])
if mode == 'bad-tour':
    graph['tour'][0]['nodeIds'] = ['absent']
if mode != 'unchanged':
    (ua / 'knowledge-graph.json').write_text(json.dumps(graph))
files = ['src/alpha/core.py', 'src/unbound.py']
(ua / 'meta.json').write_text(json.dumps({'lastAnalyzedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'analyzedFiles': len(files), 'gitCommitHash': inputs['source_snapshot']['head']}))
(ua / 'fingerprints.json').write_text(json.dumps({'gitCommitHash': inputs['source_snapshot']['head'], 'files': {p: {'contentHash': hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()} for p in files}}))
(ua / 'intermediate').mkdir(exist_ok=True)
(ua / 'intermediate/scan-result.json').write_text(json.dumps({'files': [{'path': p} for p in files]}))
(run / 'completion.json').write_text(json.dumps({
    'input_digest': inputs['input_digest'], 'status': 'partial' if mode == 'partial' else 'complete',
    'skipped_phases': [], 'issues': [],
}))
if mode == 'wrong-fingerprint':
    fp = json.loads((ua / 'fingerprints.json').read_text())
    fp['files'][files[0]]['contentHash'] = 'old'
    (ua / 'fingerprints.json').write_text(json.dumps(fp))
if mode == 'stale-meta':
    meta = json.loads((ua / 'meta.json').read_text())
    meta['lastAnalyzedAt'] = '2000-01-01T00:00:00Z'
    (ua / 'meta.json').write_text(json.dumps(meta))
if mode == 'wrong-report':
    (run / 'completion.json').write_text(json.dumps({'input_digest': 'old', 'status': 'complete', 'issues': [], 'skipped_phases': []}))
print(json.dumps({'is_error': False, 'permission_denials': ['Bash'] if mode == 'permission' else []}))
"""


@unittest.skipUnless(
    os.name == "posix" and shutil.which("node"), "POSIX native host and Node required"
)
class UaAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "project with spaces"
        self.root.mkdir()
        build_project(self.root)
        (self.root / "src/unbound.py").write_text("# not registered to any module\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        )
        self.plugin = self.base / "plugin with spaces"
        for directory in (".claude-plugin", "skills/understand", "packages/core/dist"):
            (self.plugin / directory).mkdir(parents=True)
        (self.plugin / ".claude-plugin/plugin.json").write_text(
            json.dumps({"name": "understand-anything", "version": "2.9.6"})
        )
        (self.plugin / "skills/understand/SKILL.md").write_text(
            "Native UA test fixture\n"
        )
        (self.plugin / "package.json").write_text('{"type":"module"}')
        # The bridge calls the native schema, not a copied Python schema. This fake is
        # an invocation probe, not proof of compatibility with a real UA release.
        (self.plugin / "packages/core/dist/index.js").write_text(
            "export const KnowledgeGraphSchema = {safeParse: g => ({success: g.version === '1.0.0' && g.nodes.every(n => ['simple','moderate','complex'].includes(n.complexity)), error: {issues: ['bad graph']}})};\n"
        )
        self.host = self.base / "fake-claude"
        self.host.write_text(FAKE_HOST)
        self.host.chmod(0o755)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def run_analysis(self, mode="success", **kwargs):
        with patch.dict(os.environ, {"UA_FAKE_MODE": mode}):
            return analyze_ua(
                self.root,
                plugin_root=str(self.plugin),
                claude=str(self.host),
                approve_native_tools=True,
                **kwargs,
            )

    def read_run(self, result, name):
        run = next(
            path for path in result.artifacts if path.startswith(".concorde/runs/ua-")
        )
        return json.loads((self.root / run / name).read_text())

    @verifies("scenario.views.ua-analysis-input")
    def test_prepare_only_keeps_existing_graph_and_complete_context(self):
        ua = self.root / ".ua"
        ua.mkdir()
        (ua / "knowledge-graph.json").write_text('{"old": true}')
        result = self.run_analysis(prepare_only=True)
        self.assertEqual("success", result.status, result.findings)
        self.assertEqual("prepared", result.result["analysis_status"])
        inputs = self.read_run(result, "input.json")
        self.assertIn("src/unbound.py", inputs["source_snapshot"]["files"])
        self.assertTrue(inputs["spec_context"]["protocol"]["sources"])
        for module in inputs["spec_context"]["modules"]:
            records = module["spec_context"]["sources"]
            self.assertEqual({"reading", "metadata"}, {r["role"] for r in records})
            self.assertTrue(all(r["digest"] and r["owner"] for r in records))
        self.assertEqual('{"old": true}', (ua / "knowledge-graph.json").read_text())
        self.assertFalse((self.root / result.result["run"] / "observed.json").exists())

    @verifies("scenario.views.ua-analysis-native-host")
    def test_native_analysis_follows_a_bounded_probe_with_seed_specs_and_code(self):
        result = self.run_analysis(model="test-model")
        self.assertEqual("success", result.status, result.findings)
        observed = self.read_run(result, "observed.json")
        self.assertEqual("1", observed["redirect"])
        self.assertEqual(str(self.root), observed["cwd"])
        self.assertIn("--plugin-dir", observed["argv"])
        self.assertIn("test-model", observed["argv"])
        self.assertIn("--settings", observed["argv"])
        self.assertIn("--add-dir", observed["argv"])
        probe = self.read_run(result, "observed-probe.json")
        self.assertIn("--max-budget-usd", probe["argv"])
        self.assertIn("0.50", probe["argv"])
        settings = self.read_run(result, "native-settings.json")
        self.assertNotIn("Bash", settings["permissions"]["allow"])
        self.assertNotIn("hooks", settings)
        self.assertIn("Bash(git commit *)", settings["permissions"]["deny"])
        self.assertIn(
            f"Bash(git -C {self.root} status *)", settings["permissions"]["allow"]
        )
        self.assertIn("status --porcelain", probe["prompt"])
        self.assertNotIn("--dangerously-skip-permissions", observed["argv"])
        self.assertNotIn("--setting-sources", observed["argv"])
        self.assertIn("--full", observed["prompt"])
        self.assertIn("unbound code", observed["prompt"])
        self.assertIn("BEFORE architecture", observed["prompt"])
        self.assertEqual("complete", self.read_run(result, "receipt.json")["status"])
        graph = json.loads((self.root / ".ua/knowledge-graph.json").read_text())
        self.assertTrue(any(n["id"] == "file:src/unbound.py" for n in graph["nodes"]))
        self.assertTrue(
            any(n["summary"] == "Enriched by native host" for n in graph["nodes"])
        )

    @verifies("scenario.views.ua-analysis-permission-probe")
    def test_explicit_consent_and_authentication_are_required(self):
        result = analyze_ua(
            self.root, plugin_root=str(self.plugin), claude=str(self.host)
        )
        self.assertEqual("failed", result.status)
        self.assertIn("--approve-native-tools", result.findings[0].message)
        self.assertFalse((self.root / ".concorde/runs").exists())
        result = self.run_analysis("unauthenticated")
        self.assertEqual("failed", result.status)
        run = self.root / result.artifacts[0]
        self.assertFalse((run / "observed-probe.json").exists())
        self.assertFalse((run / "observed.json").exists())

    @verifies("scenario.views.ua-analysis-permission-probe")
    def test_probe_failure_never_launches_full_analysis(self):
        for mode in ("probe-permission", "probe-missing-child"):
            with self.subTest(mode=mode):
                result = self.run_analysis(mode)
                self.assertEqual("failed", result.status)
                run = self.root / result.artifacts[0]
                self.assertTrue((run / "probe-host.json").exists())
                self.assertFalse((run / "observed.json").exists())

    @verifies("scenario.views.ua-analysis-permission-probe")
    def test_probe_only_retains_prior_scratch_without_advancing_graph(self):
        tmp = self.root / ".ua/tmp"
        tmp.mkdir(parents=True)
        (tmp / "old.json").write_text("old evidence")
        graph = self.root / ".ua/knowledge-graph.json"
        graph.write_text('{"old":true}')
        result = self.run_analysis(probe_only=True)
        self.assertEqual("success", result.status, result.findings)
        self.assertEqual("probe_passed", result.result["analysis_status"])
        run = self.root / result.result["run"]
        archive = run / "previous-scratch/tmp/old.json"
        self.assertEqual("old evidence", archive.read_text())
        self.assertEqual('{"old":true}', graph.read_text())
        self.assertFalse((run / "observed.json").exists())

    @verifies("scenario.views.ua-analysis-output-gate")
    def test_partial_invalid_and_changed_inputs_never_succeed(self):
        for mode in (
            "partial",
            "missing-seed",
            "lost-relation",
            "dangling",
            "bad-layer",
            "lost-code",
            "permission",
            "mutate-code",
            "mutate-spec",
            "native-schema",
            "duplicate-node",
            "bad-tour",
            "wrong-fingerprint",
            "stale-meta",
            "wrong-report",
        ):
            with self.subTest(mode=mode):
                result = self.run_analysis(mode)
                self.assertEqual("failed", result.status)
                self.assertEqual(
                    "failed", self.read_run(result, "receipt.json")["status"]
                )
                self.assertFalse(
                    (self.root / ".concorde/runs/ua-analysis.lock").exists()
                )

    @verifies("scenario.views.ua-analysis-output-gate")
    def test_old_graph_is_not_a_successful_new_run(self):
        first = self.run_analysis()
        self.assertEqual("success", first.status, first.findings)
        second = self.run_analysis("unchanged")
        self.assertEqual("failed", second.status)
        self.assertIn("unchanged", second.findings[0].message)
        self.assertTrue(self.read_run(second, "previous-graph.json"))

    @verifies("scenario.views.ua-analysis-failure")
    def test_host_error_and_timeout_keep_diagnostics(self):
        for mode in ("error", "timeout"):
            with self.subTest(mode=mode):
                result = self.run_analysis(mode, timeout=1)
                self.assertEqual("failed", result.status)
                self.assertEqual(
                    "failed", self.read_run(result, "receipt.json")["status"]
                )
                run = self.root / result.artifacts[0]
                self.assertTrue((run / "host.stderr").is_file())
                if mode == "timeout" and Path("/proc").is_dir():
                    child_pid = self.read_run(result, "child.json")["pid"]
                    state = Path(f"/proc/{child_pid}/stat")
                    if state.exists():
                        self.assertEqual("Z", state.read_text().split(") ", 1)[1][0])
                self.assertFalse(
                    (self.root / ".concorde/runs/ua-analysis.lock").exists()
                )

    @verifies("scenario.views.ua-analysis-failure")
    def test_interruption_records_failure_and_releases_lock(self):
        with patch(
            "concorde.views.ua_analysis._run_host", side_effect=KeyboardInterrupt
        ):
            result = self.run_analysis()
        self.assertEqual("failed", result.status)
        self.assertIn(
            "KeyboardInterrupt", self.read_run(result, "receipt.json")["error"]
        )
        self.assertFalse((self.root / ".concorde/runs/ua-analysis.lock").exists())

    @verifies("scenario.views.ua-analysis-admission")
    def test_wrong_plugin_and_concurrent_run_are_rejected(self):
        manifest = self.plugin / ".claude-plugin/plugin.json"
        original = manifest.read_text()
        manifest.write_text('{"name":"understand-anything","version":"99.0.0"}')
        result = self.run_analysis()
        self.assertEqual("failed", result.status)
        self.assertFalse((self.root / ".concorde/runs").exists())
        manifest.write_text(original)
        lock = self.root / ".concorde/runs/ua-analysis.lock"
        lock.mkdir(parents=True)
        result = self.run_analysis()
        self.assertEqual("failed", result.status)
        self.assertTrue(lock.is_dir())

    @verifies("scenario.views.ua-analysis-admission")
    def test_unsafe_or_ambiguous_graph_paths_are_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / ".ua").symlink_to(outside, target_is_directory=True)
        self.assertEqual("failed", self.run_analysis().status)
        self.assertFalse(list(outside.iterdir()))
        (self.root / ".ua").unlink()
        (self.root / ".ua").mkdir()
        (self.root / ".ua/intermediate").symlink_to(outside, target_is_directory=True)
        self.assertEqual("failed", self.run_analysis().status)
        self.assertFalse(list(outside.iterdir()))
        (self.root / ".ua/intermediate").unlink()
        (self.root / ".ua/knowledge-graph.json").write_text("{}")
        (self.root / ".understand-anything").mkdir()
        self.assertEqual("failed", self.run_analysis().status)

    @verifies("scenario.views.ua-analysis-native-host")
    def test_native_legacy_directory_is_used(self):
        (self.root / ".understand-anything").mkdir()
        result = self.run_analysis()
        self.assertEqual("success", result.status, result.findings)
        self.assertTrue(
            (self.root / ".understand-anything/knowledge-graph.json").is_file()
        )
        self.assertFalse((self.root / ".ua").exists())

    @verifies("scenario.views.ua-analysis-admission")
    def test_cli_primary_worktree_requires_explicit_permission(self):
        args = [
            "--project-root",
            str(self.root),
            "ua-analyze",
            "--ua-plugin-root",
            str(self.plugin),
            "--claude",
            str(self.host),
            "--prepare-only",
        ]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertNotEqual(0, main(args))
        self.assertFalse((self.root / ".concorde/runs").exists())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, main([*args, "--allow-primary-worktree"]))


if __name__ == "__main__":
    unittest.main()
