"""Opt-in native host permissions and bounded live admission for UA analysis.

This is an interpreter/tool grant, not an OS sandbox. Project/managed denials and
hooks remain active. Native analysis is unchanged; destructive housekeeping is not
part of this developer-facing profile.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path


def native_settings(root: Path, plugin: Path, run_dir: Path, ua_dir: str) -> dict:
    """Build a run-local overlay; never replace project or user settings."""
    data = root / ua_dir
    if any(
        character in str(path)
        for path in (root, plugin, run_dir)
        for character in "*?[]()\n\r"
    ):
        raise ValueError(
            "Native permission paths cannot contain glob/rule metacharacters"
        )
    return {
        "permissions": {
            "allow": [
                f"Read(/{plugin}/**)",
                f"Edit(/{data}/**)",
                f"Edit(/{run_dir}/completion.json)",
                f"Edit(/{run_dir}/probe-parent.json)",
                f"Edit(/{run_dir}/probe-child.json)",
                # The native flow executes both installed scripts and generated glue.
                # File-tool scopes cannot sandbox these interpreters; consent is explicit.
                "Bash(node *)",
                "Bash(python *)",
                "Bash(python3 *)",
                f"Bash(mkdir -p {data}/*)",
                f"Bash(mkdir -p {shlex.quote(str(data))}/*)",
                f"Bash(mkdir -p {ua_dir}/*)",
                "Bash(git rev-parse *)",
                f"Bash(git -C {root} rev-parse *)",
                f"Bash(git -C {shlex.quote(str(root))} rev-parse *)",
                "Bash(git status *)",
                f"Bash(git -C {root} status *)",
                f"Bash(git -C {shlex.quote(str(root))} status *)",
            ],
            "deny": [
                f"Edit(/{plugin}/**)",
                "Bash(git add *)",
                "Bash(git commit *)",
                "Bash(git push *)",
            ],
        },
    }


def profile_prompt(root: Path, plugin: Path, run_dir: Path, ua_dir: str) -> str:
    return f"""Concorde's operator-approved, analysis-only UA native host profile:
- Project: {root}. Plugin: {plugin}. UA artifacts: {root / ua_dir}.
- The explicit --approve-native-tools request grants this process and its native
  children Read access to this plugin, file-tool writes under the UA artifact
  directory and the named run reports, and Node/Python interpreter execution for
  UA's installed scripts and generated analysis glue. It is NOT a filesystem
  sandbox and grants no source, Spec, plugin, settings, hooks, git/index or other
  workspace mutations. Project and managed settings/denials/hooks remain active.
- The host has prepared the native intermediate/tmp directories and Git identity.
  Read {run_dir / "native-preflight.json"} for those admitted facts. Do not repeat
  shell preflight, environment-variable diagnostics or entry-point shell loops.
  For entry-point selection, inspect the native scan inventory or use Read/Glob.
- This profile deliberately disables UA trash purging, scratch cleanup, hook setup,
  dependency installation, worktree redirection and dashboard/browser launch.
  These maintenance/UI side effects are NOT required analysis phases and must not
  be attempted. Keep scan, batches and review evidence after successful saving.
- Run all native ANALYSIS phases, including the upstream scanner, batcher, parser,
  agents, merge, architecture, tour, validation, fingerprints and metadata save.
  Invoke the installed understand-anything:understand Skill; do not reimplement
  its scanner/parser or replace a failed phase with a homegrown alternative.
- Use plain commands with concrete paths, not compound shell scripts, shell
  variable expansion, heredocs, for-loops or find -exec. Run installed scripts
  directly. Write native inline JavaScript/Python glue as files under UA tmp and
  execute those files. Python3 may run the installed Python merge script.
- A permission denial or missing native dependency is a HARD STOP. No spelling,
  tool, interpreter, host, or homegrown-algorithm fallback after a denial. Write
  a failed run report and stop promptly; do not explore ways around it.
- Forward this complete profile to EVERY native child. Do not invoke concorde-*
  Skills. Do not commit. Do not treat a saved partial graph as completion.
"""


def prepare_native_workspace(root: Path, run_dir: Path, ua_dir: str, head: str) -> dict:
    """Keep prior attempts intact and ensure no stale batch can enter the next merge."""
    data = root / ua_dir
    archive = run_dir / "previous-scratch"
    for name in ("intermediate", "tmp"):
        path = data / name
        if path.exists():
            if not path.is_dir():
                raise ValueError(f"Native UA {name} must be a directory")
            archive.mkdir(parents=True, exist_ok=True)
            path.rename(archive / name)
        path.mkdir(parents=True)
    return {
        "project_root": str(root),
        "git_commit": head,
        "ua_directory": ua_dir,
        "intermediate_directory": str(data / "intermediate"),
        "tmp_directory": str(data / "tmp"),
        "plugin_built": True,
        "no_worktree_redirect": True,
        "retained_previous_scratch": str(archive) if archive.exists() else None,
        "disabled_side_effects": [
            "trash_purge",
            "scratch_cleanup",
            "auto_update_setup",
            "viewer_launch",
        ],
    }


def probe_prompt(
    root: Path, plugin: Path, run_dir: Path, ua_dir: str, nonce: str
) -> str:
    """A small real-host/child probe, not another whole-project cognition pass."""
    scanner = plugin / "skills/understand/scan-project.mjs"
    scan_output = root / ua_dir / "tmp/concorde-permission-scan.json"
    scan_command = shlex.join(
        [
            "node",
            str(scanner),
            str(root),
            str(scan_output),
            "--exclude",
            ".ua/**,.understand-anything/**,.concorde/runs/**",
        ]
    )
    git_command = shlex.join(["git", "-C", str(root), "rev-parse", "HEAD"])
    status_command = shlex.join(["git", "-C", str(root), "status", "--porcelain"])
    report = json.dumps({"nonce": nonce, "status": "complete"})
    return f"""CONCORDE_UA_PERMISSION_PROBE
Probe run directory: {json.dumps(str(run_dir))}
Probe nonce: {nonce}
This is a bounded permission probe, NOT the full UA analysis. Do not read Specs,
seed graphs, source bodies or the full input manifest. Do not load any Skills.
Do not write a graph, fingerprints, metadata, settings or hooks. No installation.

1. Use Read to read {plugin / ".claude-plugin/plugin.json"}.
2. Run exactly this single Bash command: {git_command}
   Then in a separate Bash call run: {status_command}
3. Run exactly this native scanner command: {scan_command}
   This is a deterministic scan for the permission probe only, not a new graph.
4. Dispatch ONE native general-purpose child (not an isolated worktree). Pass the
   complete host profile and ask it only to read the same plugin.json, run
   `node --version`, and Write {report} to {run_dir / "probe-child.json"}.
   Wait for that child. It must report any denial; do not retry or fall back.
5. If and only if all actions succeed, Write {report} to
   {run_dir / "probe-parent.json"} and finish with a short success message.

Every refusal or execution error is a hard stop. Do not try another command form.
Both reports are required. Do not claim success without the real child and native
scanner invocation. The subsequent full analysis is a separate host invocation.
"""
