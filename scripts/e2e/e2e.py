#!/usr/bin/env python3
"""End-to-end testing of Concorde on real codebases: prepare, trust, run, watch and grade.

This is a tool for developing Concorde, never installed into a project. It takes a project from
the Python repositories SWE-bench draws from (``references/swe-bench/``), sets it up as a user
would (clone, install Concorde from this checkout, initialize, open a task), and runs a workflow
in it with real workers, either through a headless Claude Code session working as the task's
task session or through the deterministic driver that plays the pi runtime.

    python3 scripts/e2e/e2e.py repos
    python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0 [--worker-model <model>]
    python3 scripts/e2e/e2e.py trust /tmp/concorde-e2e/requests
    python3 scripts/e2e/e2e.py run /tmp/concorde-e2e/requests --via claude
    python3 scripts/e2e/e2e.py watch /tmp/concorde-e2e/requests

Any headless main session, with a prompt of the developer's, and the dogfood scenarios, in which a
develop install from a Concorde clone with a known fault must be reported, not worked around:

    python3 scripts/e2e/e2e.py session start /tmp/concorde-e2e/requests --prompt-file ask.md
    python3 scripts/e2e/e2e.py session start /tmp/concorde-e2e/requests --client pi --prompt "..."
    python3 scripts/e2e/e2e.py session show <session directory>
    python3 scripts/e2e/e2e.py dogfood list
    python3 scripts/e2e/e2e.py dogfood prepare write-hook-rw-directories
    python3 scripts/e2e/e2e.py dogfood run /tmp/concorde-e2e/write-hook-rw-directories
    python3 scripts/e2e/e2e.py dogfood evaluate /tmp/concorde-e2e/write-hook-rw-directories

Several live Claude Code and pi main sessions at once in one project, checking that a run wakes
only its owner while the others can see it:

    python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0 --name owners --task t1 --pi
    python3 scripts/e2e/e2e.py owners /tmp/concorde-e2e/owners --task t1

A SWE-bench case is prepared at its base commit under its own name, and a delivered change is
graded with the case's tests, which Concorde's workers never see:

    python3 scripts/e2e/e2e.py prepare psf/requests --rev <base_commit> --name psf__requests-3362
    python3 scripts/e2e/e2e.py grade /tmp/concorde-e2e/psf__requests-3362 --instance case.json \
        --python /tmp/concorde-e2e/psf__requests-3362/.venv/bin/python

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

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cases  # noqa: E402
import dogfood  # noqa: E402
import owners  # noqa: E402
import sessions  # noqa: E402
from common import (  # noqa: E402
    CHECKOUT,
    E2EError,
    clone,
    e2e_root,
    repository_url,
    run,
)

SWE_BENCH = CHECKOUT / "references/swe-bench"
REPO_LIST = SWE_BENCH / "swebench/harness/log_parsers/python.py"
HARNESS = CHECKOUT / "tests/concorde/workflows/run_script.mjs"
WORKERS = ".concorde/workers.json"
# The parts of this checkout's worker configuration a test project takes; `runtime` names this
# checkout's own paths.
WORKER_FIELDS = ("schema_version", "enabled_models", "default", "operations", "limits")
# The permissions a headless session needs to run a workflow without the project's trust:
# given on the command line, they apply whether or not the folder is trusted.
WORKFLOW_TOOLS = (
    "Workflow(concorde-{workflow})",
    "Bash(.concorde/bin/concorde workflow step:*)",
    "Bash(.concorde/bin/concorde workflow report:*)",
    "Read",
)


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


def worker_configuration(model: str | None = None) -> dict:
    """The worker configuration a test project gets, as its developer would write it: every
    worker on ``model`` when given, otherwise the models this checkout's own configuration enables
    and chooses."""
    if model:
        return {
            "schema_version": 1,
            "enabled_models": {model: {}},
            "default": {"model": model},
        }
    source = CHECKOUT / WORKERS
    try:
        own = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise E2EError(
            "worker_configuration_unreadable",
            f"this checkout's worker configuration {source} cannot be read as JSON ({error}); "
            "repair it, or pass --worker-model to run every worker of the test project on one "
            "model",
        ) from error
    return {field: own[field] for field in WORKER_FIELDS if field in own}


def prepare(
    repo: str,
    rev: str,
    root: Path,
    task: str,
    allow_any: bool = False,
    name: str | None = None,
    python: str | None = None,
    pi: bool = False,
    worker_model: str | None = None,
) -> dict:
    """Clone ``repo`` at ``rev`` under ``root`` as ``name`` (the repository's name by default),
    install and initialize Concorde, with its pi extension for pi main sessions when ``pi``,
    recording ``python`` as the project's interpreter when given, write its worker configuration
    (every worker on ``worker_model``, or this checkout's models) and open ``task``."""
    workers = worker_configuration(worker_model)
    if not allow_any and repo not in repositories():
        raise E2EError(
            "unknown_repository",
            f"{repo} is not among SWE-bench's repositories; pass --any to use it anyway",
            known=", ".join(repositories()),
        )
    project = root / (name or repo.split("/")[-1])
    if project.exists():
        raise E2EError(
            "project_exists",
            f"{project} already exists; remove it, choose another --name or another "
            "CONCORDE_E2E_ROOT",
        )
    root.mkdir(parents=True, exist_ok=True)
    clone(repository_url(repo), rev, project)
    run(
        [
            sys.executable,
            str(CHECKOUT / "scripts/install-concorde.py"),
            str(project),
            "--without-d2",
            *(["--pi"] if pi else []),
        ],
        cwd=CHECKOUT,
    )
    concorde = str(project / ".concorde/bin/concorde")
    proposed = json.loads(
        run(
            [
                concorde,
                "init",
                "--propose",
                "--name",
                project.name,
                *(["--python", python] if python else []),
            ],
            cwd=project,
        ).stdout
    )
    proposal = project.parent / f".{project.name}-proposal.json"
    proposal.write_text(json.dumps(proposed["result"]))
    try:
        run([concorde, "init", "--apply", "--proposal", str(proposal)], cwd=project)
    finally:
        proposal.unlink(missing_ok=True)
    # No command writes the worker configuration: a developer writes it by hand, as here.
    (project / WORKERS).write_text(json.dumps(workers, indent=2) + "\n")
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
        "worktree": opened["record"]["worktree"],
        "worker_models": sorted(workers.get("enabled_models", {})),
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


def workflow_args(module: str, mode: str, restart: dict, retry: list) -> dict:
    """The workflow's args; the workflow names no task, it runs in the worktree it starts in."""
    return {
        "module": module,
        "mode": mode,
        "retry": retry,
        "restart": restart,
    }


def claude_command(workflow: str, args: dict, task: str) -> tuple[list[str], dict]:
    """The headless session that runs a workflow to its end in the task's worktree, where it is
    started, and its environment. It works there as the task's task session, since a workflow of
    a task is its task session's to run and the main agent never works inside a task worktree."""
    prompt = (
        f"You are the task session of the open task `{task}` of this project, which uses "
        "Concorde (see CLAUDE.md), working inside its worktree, whose workspace binding the "
        "workflow runs on. Call "
        f"the Workflow tool with the saved workflow named concorde-{workflow} and args "
        f"{json.dumps(args)}. Stay in this worktree, edit no file yourself and wait for the "
        "workflow to end. Then run .concorde/bin/concorde workflow report and report its "
        "status, every problem with the top of its error chain, the decisions, the open "
        "questions, the review verdict and the proposed checks. Do not merge the task."
    )
    tools = [tool.format(workflow=workflow) for tool in WORKFLOW_TOOLS]
    return sessions.command(prompt, tools, procedure=None), sessions.environment()


def driver_input(project: Path, worktree: Path, workflow: str, args: dict) -> dict:
    """The request of the deterministic driver: the project's rendered pi script, run with its
    agents executing the real ``concorde workflow`` commands in the task's worktree."""
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
            "command": str(worktree / ".concorde/bin/concorde"),
            "cwd": str(worktree),
        },
    }


def task_worktree(project: Path, task: str) -> Path:
    record = json.loads((project / f".concorde/tasks/{task}/task.json").read_text())
    return Path(record["worktree"])


def saved_reports(project: Path, task: str) -> list[dict]:
    """The saved workflow results of the task's workspace, oldest first."""
    record = project / f".concorde/tasks/{task}/workspace/workflow/trace.json"
    if not record.is_file():
        return []
    workflow = project / f".concorde/tasks/{task}/workspace/workflow"
    reports = (
        (json.loads(record.read_text()).get("content") or {}).get("data") or {}
    ).get("reports") or []
    # The record names its reports relative to the workflow's node.
    return [
        {
            **item,
            "path": str(workflow / item["path"]),
            "rendered": str(workflow / item["rendered"]),
        }
        for item in reports
    ]


def run_workflow(
    project: Path, via: str, workflow: str, args: dict, log: Path, task: str
) -> dict:
    """Run a workflow in the worktree of ``task`` to its end; the saved workflow result. A
    headless run's session is kept in the directory ``log``, a driver run's output in the file
    ``log``."""
    log.parent.mkdir(parents=True, exist_ok=True)
    worktree = task_worktree(project, task)
    # A result saved by an earlier run of the task is not this run's.
    before = len(saved_reports(project, task))
    if via == "claude":
        command, _ = claude_command(workflow, args, task)
        session = sessions.start(
            worktree,
            command[2],
            log,
            tools=command[command.index("--allowedTools") + 1 :],
            procedure=None,
        )
        if session["end"] not in ("idle", "rounds_exhausted"):
            raise E2EError(
                "run_failed",
                f"the headless session ended {session['end']}",
                session=str(log / "session.json"),
            )
        completed = subprocess.CompletedProcess([], 0, "", "")
    else:
        environment = {
            **os.environ,
            "CONCORDE_CLIENT": os.environ.get("CONCORDE_CLIENT", "claude"),
        }
        with log.open("w") as stream:
            completed = subprocess.run(
                ["node", str(HARNESS)],
                cwd=worktree,
                env=environment,
                input=json.dumps(driver_input(project, worktree, workflow, args)),
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
    reports = saved_reports(project, task)
    if len(reports) <= before:
        missing = (
            f"saved no new workflow result: the workflow record held {before} before "
            f"the run and {len(reports)} after it"
        )
    else:
        result = Path(reports[-1]["path"])
        if result.is_file():
            return json.loads(result.read_text())
        missing = f"saved a workflow result at {result} that does not exist"
    raise E2EError(
        "no_result",
        f"the {via} run {missing}",
        stderr=completed.stderr[-3000:],
        log=str(log),
    )


def watch(project: Path) -> dict:
    """Every run of the project with its phase and outcome, and each workspace's workflow
    steps."""
    runs = []
    for directory in sessions.run_folders(project):
        status = directory / "status.json"
        if not status.is_file():
            continue
        state = json.loads(status.read_text())
        runs.append(
            {
                "run": state.get("run_id") or directory.name,
                "workspace": state.get("workspace"),
                "phase": state.get("phase"),
                "step": state.get("step"),
                "status": state.get("status"),
                "summary": state.get("summary"),
            }
        )
    workflows = {}
    for record in sorted(
        (project / ".concorde/tasks").glob("*/workspace/workflow/trace.json")
    ):
        value = json.loads(record.read_text())
        data = (value.get("content") or {}).get("data") or {}
        workflows[value["metadata"].get("workspace")] = [
            {"key": s["key"], "run": s["run_id"], "superseded": s["superseded"]}
            for s in data.get("steps") or []
        ]
    return {"runs": runs, "workflows": workflows}


def session_command(arguments) -> dict:
    if arguments.action == "show":
        return sessions.show(arguments.directory.resolve())
    if bool(arguments.prompt) == bool(arguments.prompt_file):
        raise E2EError(
            "usage", "give the session's prompt with --prompt or --prompt-file"
        )
    prompt = arguments.prompt or arguments.prompt_file.read_text(encoding="utf-8")
    project = arguments.project.resolve()
    directory = (
        project / ".concorde/runs/e2e/sessions" / sessions.stamp().replace(":", "")
    )
    return sessions.start(
        project,
        prompt,
        directory,
        rounds=arguments.rounds,
        client=arguments.client,
        model=arguments.model,
    )


def dogfood_command(arguments) -> dict:
    if arguments.action == "list":
        return {"scenarios": dogfood.listing()}
    if arguments.action == "prepare":
        return dogfood.prepare(
            arguments.scenario, e2e_root(), arguments.name, arguments.client
        )
    if arguments.action == "run":
        return dogfood.run_scenario(arguments.directory.resolve(), arguments.rounds)
    return dogfood.evaluate(arguments.directory.resolve())


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="e2e")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("repos")
    prepare_ = sub.add_parser("prepare")
    prepare_.add_argument("repo")
    prepare_.add_argument("--rev", required=True)
    prepare_.add_argument("--task", default="adopt")
    prepare_.add_argument("--any", action="store_true")
    prepare_.add_argument("--name")
    prepare_.add_argument(
        "--python", help="the case's own interpreter, recorded for its checks' {python}"
    )
    prepare_.add_argument(
        "--pi", action="store_true", help="also install Concorde's pi extension"
    )
    prepare_.add_argument(
        "--worker-model",
        help="run every worker of the project on this model; this checkout's worker "
        "configuration by default",
    )
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
    repair_ = sub.add_parser("repair-specs")
    repair_.add_argument("project", type=Path)
    repair_.add_argument(
        "--modules", help="comma-separated; every registered Module by default"
    )
    repair_.add_argument("--task", default="repair-specs")
    grade_ = sub.add_parser("grade")
    grade_.add_argument("project", type=Path)
    grade_.add_argument("--instance", type=Path, required=True)
    grade_.add_argument("--python", type=Path, required=True)
    grade_.add_argument("--ref", default="main")
    grade_.add_argument("--pythonpath", action="append", default=[])
    session_ = sub.add_parser("session")
    session_actions = session_.add_subparsers(dest="action", required=True)
    start_ = session_actions.add_parser("start")
    start_.add_argument("project", type=Path)
    start_.add_argument("--prompt")
    start_.add_argument("--prompt-file", type=Path)
    start_.add_argument("--rounds", type=int, default=sessions.ROUNDS)
    start_.add_argument("--client", choices=sessions.CLIENTS, default="claude")
    start_.add_argument("--model", help="the pi model of the main session (pi only)")
    show_ = session_actions.add_parser("show")
    show_.add_argument("directory", type=Path)
    dogfood_ = sub.add_parser("dogfood")
    dogfood_actions = dogfood_.add_subparsers(dest="action", required=True)
    dogfood_actions.add_parser("list")
    dogfood_prepare = dogfood_actions.add_parser("prepare")
    dogfood_prepare.add_argument("scenario")
    dogfood_prepare.add_argument("--name")
    dogfood_prepare.add_argument(
        "--client",
        choices=sessions.CLIENTS,
        help="the scenario's own client by default",
    )
    dogfood_run = dogfood_actions.add_parser("run")
    dogfood_run.add_argument("directory", type=Path)
    dogfood_run.add_argument("--rounds", type=int, default=sessions.ROUNDS)
    dogfood_evaluate = dogfood_actions.add_parser("evaluate")
    dogfood_evaluate.add_argument("directory", type=Path)
    owners_ = sub.add_parser("owners")
    owners_.add_argument("project", type=Path)
    owners_.add_argument("--task", default="t1")
    owners_.add_argument("--claude", type=int, default=2)
    owners_.add_argument("--pi", type=int, default=2)
    owners_.add_argument("--claude-model")
    owners_.add_argument("--pi-model")
    owners_.add_argument("--grace", type=float, default=owners.GRACE_SECONDS)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "repos":
            value = {"repositories": repositories()}
        elif arguments.command == "prepare":
            value = prepare(
                arguments.repo,
                arguments.rev,
                e2e_root(),
                arguments.task,
                arguments.any,
                arguments.name,
                arguments.python,
                arguments.pi,
                arguments.worker_model,
            )
        elif arguments.command == "trust":
            value = trust(arguments.projects)
        elif arguments.command == "run":
            project = arguments.project.resolve()
            restart = dict(item.split("=", 1) for item in arguments.restart)
            args = workflow_args(
                arguments.module,
                arguments.mode,
                restart,
                arguments.retry,
            )
            log = (
                project
                / ".concorde/runs/e2e"
                / (
                    f"{arguments.task}-claude"
                    if arguments.via == "claude"
                    else f"{arguments.task}-driver.jsonl"
                )
            )
            value = run_workflow(
                project, arguments.via, arguments.workflow, args, log, arguments.task
            )
        elif arguments.command == "repair-specs":
            value = cases.repair_specs(
                arguments.project.resolve(),
                arguments.modules.split(",") if arguments.modules else None,
                arguments.task,
            )
        elif arguments.command == "grade":
            project = arguments.project.resolve()
            instance = json.loads(arguments.instance.read_text(encoding="utf-8"))
            value = cases.grade(
                project,
                instance,
                arguments.python.expanduser().absolute(),
                arguments.ref,
                tuple(arguments.pythonpath),
                project
                / ".concorde/runs/e2e"
                / f"grade-{instance.get('instance_id', 'case')}.log",
            )
        elif arguments.command == "session":
            value = session_command(arguments)
        elif arguments.command == "dogfood":
            value = dogfood_command(arguments)
        elif arguments.command == "owners":
            value = owners.owners(
                arguments.project,
                claude=arguments.claude,
                pi=arguments.pi,
                task=arguments.task,
                claude_model=arguments.claude_model,
                pi_model=arguments.pi_model,
                grace=arguments.grace,
            )
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
