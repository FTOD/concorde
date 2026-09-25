#!/usr/bin/env python3
"""End-to-end testing of Concorde on real codebases: prepare, trust, run and watch.

This is a tool for developing Concorde, never installed into a project. It takes a project from
the Python repositories SWE-bench draws from (``references/swe-bench/``), sets it up as a user
would (clone, install Concorde from this checkout, initialize, open a task), and runs a workflow
in it with real workers, either through a headless Claude Code main session or through the
deterministic driver that plays the pi runtime.

    python3 scripts/e2e/e2e.py repos
    python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0
    python3 scripts/e2e/e2e.py trust ~/concorde-e2e/requests
    python3 scripts/e2e/e2e.py run ~/concorde-e2e/requests --via claude
    python3 scripts/e2e/e2e.py watch ~/concorde-e2e/requests

Every command prints one JSON object; a failure prints ``{"error": ...}`` with what failed, the
command and its output, and exits 1.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[2]
SWE_BENCH = CHECKOUT / "references/swe-bench"
REPO_LIST = SWE_BENCH / "swebench/harness/log_parsers/python.py"
HARNESS = CHECKOUT / "tests/concorde/workflows/run_script.mjs"
# Where prepared projects live unless CONCORDE_E2E_ROOT says otherwise. Not the home directory
# itself: Claude Code keeps no trust for a session started there.
DEFAULT_ROOT = Path.home() / "concorde-e2e"
# The permissions a headless main session needs to run a workflow without the project's trust:
# given on the command line, they apply whether or not the folder is trusted.
WORKFLOW_TOOLS = (
    "Workflow(concorde-{workflow})",
    "Bash(.concorde/bin/concorde workflow step:*)",
    "Bash(.concorde/bin/concorde workflow report:*)",
    "Read",
)
# Without it `claude -p` stops a background workflow after ten idle minutes; 0 waits without end.
WAIT_VARIABLE = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"


class E2EError(Exception):
    def __init__(self, code: str, detail: str, **evidence):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.evidence = evidence


def run(command: list[str], cwd: Path, **options) -> subprocess.CompletedProcess:
    """Run a command; ``E2EError`` names it, its exit status and its output when it fails."""
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False, **options
    )
    if completed.returncode != 0:
        raise E2EError(
            "command_failed",
            f"`{' '.join(command)}` in {cwd} exited with status {completed.returncode}",
            stdout=completed.stdout[-3000:],
            stderr=completed.stderr[-3000:],
        )
    return completed


def repositories(listing: Path = REPO_LIST) -> list[str]:
    """The Python repositories SWE-bench's harness knows, as ``owner/name``."""
    try:
        text = listing.read_text(encoding="utf-8")
    except OSError as error:
        raise E2EError(
            "swe_bench_missing",
            f"{listing} cannot be read ({error}); run "
            "python3 scripts/development/init-references.py",
        ) from error
    return sorted(set(re.findall(r'"([\w.-]+/[\w.-]+)":\s*parse_log', text)))


def e2e_root() -> Path:
    return Path(os.environ.get("CONCORDE_E2E_ROOT") or DEFAULT_ROOT).expanduser()


def prepare(
    repo: str, rev: str, root: Path, task: str, allow_any: bool = False
) -> dict:
    """Clone ``repo`` at ``rev`` under ``root``, install and initialize Concorde, open ``task``."""
    if not allow_any and repo not in repositories():
        raise E2EError(
            "unknown_repository",
            f"{repo} is not among SWE-bench's repositories; pass --any to use it anyway",
            known=", ".join(repositories()),
        )
    project = root / repo.split("/")[-1]
    if project.exists():
        raise E2EError(
            "project_exists",
            f"{project} already exists; remove it or choose another CONCORDE_E2E_ROOT",
        )
    root.mkdir(parents=True, exist_ok=True)
    run(
        [
            "git",
            "clone",
            "-q",
            "--depth",
            "1",
            "--branch",
            rev,
            f"https://github.com/{repo}.git",
            str(project),
        ],
        cwd=root,
    )
    run(["git", "checkout", "-q", "-b", "main"], cwd=project)
    run(
        [
            sys.executable,
            str(CHECKOUT / "scripts/install-concorde.py"),
            str(project),
            "--without-d2",
        ],
        cwd=CHECKOUT,
    )
    concorde = str(project / ".concorde/bin/concorde")
    proposed = json.loads(
        run([concorde, "init", "--propose", "--name", project.name], cwd=project).stdout
    )
    proposal = project.parent / f".{project.name}-proposal.json"
    proposal.write_text(json.dumps(proposed["result"]))
    try:
        run([concorde, "init", "--apply", "--proposal", str(proposal)], cwd=project)
    finally:
        proposal.unlink(missing_ok=True)
    run(["git", "add", "-A"], cwd=project)
    run(["git", "commit", "-q", "-m", "Adopt Concorde"], cwd=project)
    opened = json.loads(
        run(
            [
                concorde,
                "task",
                "open",
                task,
                "--goal",
                "Describe the existing code in Specs with the brownfield workflow",
                "--modules",
                "module.project",
            ],
            cwd=project,
        ).stdout
    )
    return {
        "project": str(project),
        "repository": repo,
        "revision": rev,
        "task": task,
        "worktree": opened["worktree"],
    }


def claude_config() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(base) / ".claude.json" if base else Path.home() / ".claude.json"


def repository_root(path: Path) -> Path:
    return Path(run(["git", "rev-parse", "--show-toplevel"], cwd=path).stdout.strip())


def trust(paths: list[Path], config: Path | None = None) -> dict:
    """Mark each project's repository root trusted in Claude Code's configuration.

    Claude Code keys workspace trust on the git repository root and ignores a parent folder's
    trust for a project's allow rules, so every prepared project needs its own entry. The file is
    backed up once, next to itself, before the first change.
    """
    config = config or claude_config()
    value = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
    projects = value.setdefault("projects", {})
    changed = []
    for path in paths:
        root = str(repository_root(path.resolve()))
        entry = projects.setdefault(root, {})
        if entry.get("hasTrustDialogAccepted") is not True:
            entry["hasTrustDialogAccepted"] = True
            changed.append(root)
    if changed:
        backup = config.with_name(config.name + ".concorde-e2e.bak")
        if config.exists() and not backup.exists():
            shutil.copy2(config, backup)
        temporary = config.with_name(config.name + ".concorde-e2e.tmp")
        temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        temporary.replace(config)
    return {
        "config": str(config),
        "trusted": changed,
        "already": [
            str(repository_root(p.resolve()))
            for p in paths
            if str(repository_root(p.resolve())) not in changed
        ],
    }


def workflow_args(
    task: str, module: str, mode: str, restart: dict, retry: list
) -> dict:
    return {
        "task": task,
        "module": module,
        "mode": mode,
        "retry": retry,
        "restart": restart,
    }


def claude_command(workflow: str, args: dict) -> tuple[list[str], dict]:
    """The headless main session that runs a workflow to its end, and its environment."""
    prompt = (
        "You are Concorde's main agent in this project (see CLAUDE.md). The task "
        f"`{args['task']}` is open. Call the Workflow tool with the saved workflow named "
        f"concorde-{workflow} and args {json.dumps(args)}. Stay in this primary worktree, edit "
        "no file yourself and wait for the workflow to end. Then read "
        f".concorde/tasks/{args['task']}.workflow.json and report its status, every problem "
        "with the top of its error chain, the decisions, the open questions, the review verdict "
        "and the proposed checks. Do not merge the task."
    )
    tools = [tool.format(workflow=workflow) for tool in WORKFLOW_TOOLS]
    command = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        *tools,
        "--output-format",
        "stream-json",
        "--verbose",
    ]
    return command, {**os.environ, WAIT_VARIABLE: "0"}


def driver_input(project: Path, workflow: str, args: dict) -> dict:
    """The request of the deterministic driver: the project's rendered pi script, run with its
    agents executing the real ``concorde workflow`` commands."""
    script = project / f".concorde/framework/generated/workflows/pi/{workflow}.js"
    if not script.is_file():
        raise E2EError("script_missing", f"{script} does not exist; reinstall Concorde")
    return {
        "script": str(script),
        "client": "pi",
        "args": args,
        "outcomes": {},
        "report": None,
        "execute": {
            "command": str(project / ".concorde/bin/concorde"),
            "cwd": str(project),
        },
    }


def run_workflow(project: Path, via: str, workflow: str, args: dict, log: Path) -> dict:
    """Run a workflow in ``project`` to its end; the saved workflow result."""
    log.parent.mkdir(parents=True, exist_ok=True)
    if via == "claude":
        command, environment = claude_command(workflow, args)
        with log.open("w") as stream:
            completed = subprocess.run(
                command,
                cwd=project,
                env=environment,
                stdout=stream,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
    else:
        environment = {
            **os.environ,
            "CONCORDE_CLIENT": os.environ.get("CONCORDE_CLIENT", "claude"),
        }
        with log.open("w") as stream:
            completed = subprocess.run(
                ["node", str(HARNESS)],
                cwd=project,
                env=environment,
                input=json.dumps(driver_input(project, workflow, args)),
                stdout=stream,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
    if completed.returncode != 0:
        raise E2EError(
            "run_failed",
            f"the {via} run exited with status {completed.returncode}",
            stderr=completed.stderr[-3000:],
            log=str(log),
        )
    result = project / f".concorde/tasks/{args['task']}.workflow.json"
    if not result.is_file():
        raise E2EError(
            "no_result",
            f"the {via} run ended without a workflow result at {result}",
            stderr=completed.stderr[-3000:],
            log=str(log),
        )
    return json.loads(result.read_text())


def watch(project: Path) -> dict:
    """Every run of the project with its phase and outcome, and each task's workflow steps."""
    runs = []
    for directory in sorted((project / ".concorde/runs").glob("r-*")):
        status = directory / "status.json"
        if not status.is_file():
            continue
        state = json.loads(status.read_text())
        runs.append(
            {
                "run": directory.name,
                "task": state.get("task"),
                "phase": state.get("phase"),
                "step": state.get("step"),
                "status": state.get("status"),
                "summary": state.get("summary"),
            }
        )
    workflows = {}
    for record in sorted((project / ".concorde/tasks").glob("*.json")):
        value = json.loads(record.read_text())
        # Only task records: the workflow result beside one names its workflow as a string.
        if isinstance(value, dict) and isinstance(value.get("workflow"), dict):
            workflows[value["id"]] = [
                {"key": s["key"], "run": s["run_id"], "superseded": s["superseded"]}
                for s in value["workflow"]["steps"]
            ]
    return {"runs": runs, "workflows": workflows}


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="e2e")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("repos")
    prepare_ = sub.add_parser("prepare")
    prepare_.add_argument("repo")
    prepare_.add_argument("--rev", required=True)
    prepare_.add_argument("--task", default="adopt")
    prepare_.add_argument("--any", action="store_true")
    trust_ = sub.add_parser("trust")
    trust_.add_argument("projects", nargs="+", type=Path)
    run_ = sub.add_parser("run")
    run_.add_argument("project", type=Path)
    run_.add_argument("--via", choices=["claude", "driver"], default="claude")
    run_.add_argument("--workflow", default="brownfield")
    run_.add_argument("--task", default="adopt")
    run_.add_argument("--module", default="module.project")
    run_.add_argument("--mode", choices=["no-ask", "interactive"], default="no-ask")
    run_.add_argument("--retry", action="append", default=[])
    run_.add_argument("--restart", action="append", default=[], metavar="KEY=LABEL")
    watch_ = sub.add_parser("watch")
    watch_.add_argument("project", type=Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "repos":
            value = {"repositories": repositories()}
        elif arguments.command == "prepare":
            value = prepare(
                arguments.repo, arguments.rev, e2e_root(), arguments.task, arguments.any
            )
        elif arguments.command == "trust":
            value = trust(arguments.projects)
        elif arguments.command == "run":
            project = arguments.project.resolve()
            restart = dict(item.split("=", 1) for item in arguments.restart)
            args = workflow_args(
                arguments.task,
                arguments.module,
                arguments.mode,
                restart,
                arguments.retry,
            )
            log = (
                project
                / ".concorde/runs/e2e"
                / f"{arguments.task}-{arguments.via}.jsonl"
            )
            value = run_workflow(project, arguments.via, arguments.workflow, args, log)
        else:
            value = watch(arguments.project.resolve())
    except E2EError as error:
        sys.stdout.write(
            json.dumps(
                {
                    "error": {
                        "code": error.code,
                        "detail": error.detail,
                        **error.evidence,
                    }
                },
                indent=2,
            )
            + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
