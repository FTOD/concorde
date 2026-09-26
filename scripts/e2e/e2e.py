#!/usr/bin/env python3
"""End-to-end testing of Concorde on real codebases: prepare, trust, run, watch and grade.

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

Any headless main session, with a prompt of the developer's, and the dogfood scenarios, in which a
develop install from a Concorde clone with a known fault must be reported, not worked around:

    python3 scripts/e2e/e2e.py session start ~/concorde-e2e/requests --prompt-file ask.md
    python3 scripts/e2e/e2e.py session show <session directory>
    python3 scripts/e2e/e2e.py dogfood list
    python3 scripts/e2e/e2e.py dogfood prepare write-hook-rw-directories
    python3 scripts/e2e/e2e.py dogfood run ~/concorde-e2e/write-hook-rw-directories
    python3 scripts/e2e/e2e.py dogfood evaluate ~/concorde-e2e/write-hook-rw-directories

A SWE-bench case is prepared at its base commit under its own name, and a delivered change is
graded with the case's tests, which Concorde's workers never see:

    python3 scripts/e2e/e2e.py prepare psf/requests --rev <base_commit> --name psf__requests-3362
    python3 scripts/e2e/e2e.py grade ~/concorde-e2e/psf__requests-3362 --instance case.json \
        --python ~/concorde-e2e/psf__requests-3362/.venv/bin/python

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
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dogfood  # noqa: E402
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
# The permissions a headless main session needs to run a workflow without the project's trust:
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


def prepare(
    repo: str,
    rev: str,
    root: Path,
    task: str,
    allow_any: bool = False,
    name: str | None = None,
    python: str | None = None,
) -> dict:
    """Clone ``repo`` at ``rev`` under ``root`` as ``name`` (the repository's name by default),
    install and initialize Concorde, recording ``python`` as the project's interpreter when
    given, and open ``task``."""
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
    return sessions.command(prompt, tools), sessions.environment()


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
    """Run a workflow in ``project`` to its end; the saved workflow result. A headless run's
    session is kept in the directory ``log``, a driver run's output in the file ``log``."""
    log.parent.mkdir(parents=True, exist_ok=True)
    if via == "claude":
        command, _ = claude_command(workflow, args)
        session = sessions.start(
            project,
            command[2],
            log,
            tools=command[command.index("--allowedTools") + 1 :],
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


# In a case the Specs are ours, added by adoption, and describe code we never change; so one
# round of repairing their review findings precedes the issue. This exception to "review gaps
# wait for a person" holds for end-to-end cases only, which is why it lives here.
REPAIR_INTENT = (
    "Repair every blocking finding of the Spec review given as input, in the documents of the "
    "Modules it names. These Specs describe the project's existing code: change what the Specs "
    "say, never the code, keep every promise true to what the code does, and where a repair "
    "would need a decision about intended behaviour, write an open question instead of a "
    "promise."
)


def concorde_run(concorde: str, worktree: Path, argv: list[str]) -> dict:
    """One Operation run in ``worktree``; its result, whatever its exit status."""
    done = subprocess.run(
        [concorde, "run", *argv],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return json.loads(done.stdout)
    except ValueError as error:
        raise E2EError(
            "unreadable_result",
            f"`concorde run {' '.join(argv)}` in {worktree} printed no JSON result "
            f"(exit {done.returncode})",
            stdout=done.stdout[-3000:],
            stderr=done.stderr[-3000:],
        ) from error


def _brief(result: dict) -> dict:
    output = result.get("output") or {}
    return {
        "run": result.get("run_id"),
        "status": result.get("status"),
        "summary": result.get("summary"),
        **({"verdict": output["verdict"]} if "verdict" in output else {}),
        **({"error": result["error"]} if result.get("error") else {}),
    }


def repair_specs(
    project: Path,
    modules: list[str] | None = None,
    task: str = "repair-specs",
    run_operation=concorde_run,
) -> dict:
    """Repair an adopted case's Specs from one review round, in a task of their own: review,
    specify with the review as input, review again, validate, deliver and merge. A step that does
    not end ok stops the repair with its result, and the task stays open."""
    concorde = str(project / ".concorde/bin/concorde")
    if modules is None:
        registry = json.loads((project / ".concorde/specs.json").read_text())
        modules = [item["id"] for item in registry["modules"]]
    bound = ",".join(modules)
    opened = json.loads(
        run(
            [
                concorde,
                "task",
                "open",
                task,
                "--goal",
                "Repair the adopted Specs' review findings before the case's issue",
                "--modules",
                bound,
            ],
            cwd=project,
        ).stdout
    )
    worktree = Path(opened["worktree"])
    steps: list[dict] = []

    def step(name: str, argv: list[str]) -> dict | None:
        result = run_operation(concorde, worktree, argv)
        steps.append({"step": name, **_brief(result)})
        return result if result.get("status") == "ok" else None

    def stopped(name: str) -> dict:
        return {"task": task, "modules": modules, "steps": steps, "stopped_at": name}

    review = step("spec_review", ["spec_review", "--task", task, "--modules", bound])
    if review is None:
        return stopped("spec_review")
    if (review.get("output") or {}).get("verdict") != "accepted":
        if (
            step(
                "specify",
                [
                    "specify",
                    "--task",
                    task,
                    "--modules",
                    bound,
                    "--input",
                    review["run_id"],
                    "--intent",
                    REPAIR_INTENT,
                ],
            )
            is None
        ):
            return stopped("specify")
        if (
            step(
                "spec_review_again", ["spec_review", "--task", task, "--modules", bound]
            )
            is None
        ):
            return stopped("spec_review_again")
    for name in ("validate", "delivery"):
        if step(name, [name, "--task", task]) is None:
            return stopped(name)
    run([concorde, "task", "merge", task], cwd=project)
    return {"task": task, "modules": modules, "steps": steps, "stopped_at": None}


RESULT_LINE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) (\S+)")
PATCHED_FILE = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)


def reset_patched_files(tree: Path, patch: str, base: str) -> list[str]:
    """Put every file ``patch`` touches back as it was at ``base``, removing the ones ``base``
    lacks, as SWE-bench does before it applies a test patch: the change under test may have
    edited the same test files, and the case's tests are graded as the case wrote them."""
    paths = sorted({path for pair in PATCHED_FILE.findall(patch) for path in pair})
    for path in paths:
        present = subprocess.run(
            ["git", "cat-file", "-e", f"{base}:{path}"],
            cwd=tree,
            capture_output=True,
            check=False,
        )
        if present.returncode == 0:
            run(["git", "checkout", "-q", base, "--", path], cwd=tree)
        else:
            (tree / path).unlink(missing_ok=True)
    return paths


def pytest_statuses(output: str) -> dict[str, str]:
    """Each test's status from the short summary that ``pytest -rA`` prints."""
    statuses: dict[str, str] = {}
    for line in output.splitlines():
        match = RESULT_LINE.match(line)
        if match:
            statuses[match.group(2)] = match.group(1)
    return statuses


def case_tests(instance: dict, field: str) -> list[str]:
    value = instance.get(field) or []
    return json.loads(value) if isinstance(value, str) else list(value)


def grade(
    project: Path,
    instance: dict,
    python: Path,
    ref: str = "main",
    pythonpath: tuple[str, ...] = (),
    log: Path | None = None,
) -> dict:
    """Grade ``ref`` of ``project`` as SWE-bench would: apply the case's test patch to a
    throwaway worktree of ``ref``, run the test files it names, and compare with the case's
    FAIL_TO_PASS and PASS_TO_PASS tests. The project itself is left as it was."""
    fail_to_pass = case_tests(instance, "FAIL_TO_PASS")
    pass_to_pass = case_tests(instance, "PASS_TO_PASS")
    if (
        not fail_to_pass
        or not instance.get("test_patch")
        or not instance.get("base_commit")
    ):
        raise E2EError(
            "invalid_case",
            f"case {instance.get('instance_id')} needs FAIL_TO_PASS tests, a test_patch and "
            "a base_commit",
        )
    scratch = Path(tempfile.mkdtemp(prefix="concorde-grade-"))
    tree = scratch / "tree"
    run(["git", "worktree", "add", "-q", "--detach", str(tree), ref], cwd=project)
    try:
        patch = scratch / "test.patch"
        patch.write_text(instance["test_patch"], encoding="utf-8")
        reset_patched_files(tree, instance["test_patch"], instance["base_commit"])
        run(["git", "apply", str(patch)], cwd=tree)
        files = sorted({test.split("::")[0] for test in fail_to_pass + pass_to_pass})
        environment = {**os.environ}
        if pythonpath:
            environment["PYTHONPATH"] = os.pathsep.join(
                str(tree / item) for item in pythonpath
            )
        command = [str(python), "-m", "pytest", "-rA", "-p", "no:cacheprovider", *files]
        completed = subprocess.run(
            command,
            cwd=tree,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tree)],
            cwd=project,
            capture_output=True,
            check=False,
        )
        shutil.rmtree(scratch, ignore_errors=True)
    output = completed.stdout + "\n" + completed.stderr
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(output, encoding="utf-8")
    statuses = pytest_statuses(completed.stdout)

    def split(tests: list[str]) -> dict:
        passed = [test for test in tests if statuses.get(test) == "PASSED"]
        others = {test: statuses.get(test, "not run") for test in tests}
        return {
            "passed": len(passed),
            "total": len(tests),
            "not_passed": {k: v for k, v in others.items() if v != "PASSED"},
        }

    f2p, p2p = split(fail_to_pass), split(pass_to_pass)
    return {
        "instance": instance.get("instance_id"),
        "ref": ref,
        "resolved": f2p["passed"] == f2p["total"] and p2p["passed"] == p2p["total"],
        "fail_to_pass": f2p,
        "pass_to_pass": p2p,
        "command": command,
        "exit_code": completed.returncode,
        "log": str(log) if log is not None else None,
    }


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
    return sessions.start(project, prompt, directory, rounds=arguments.rounds)


def dogfood_command(arguments) -> dict:
    if arguments.action == "list":
        return {"scenarios": dogfood.listing()}
    if arguments.action == "prepare":
        return dogfood.prepare(arguments.scenario, e2e_root(), arguments.name)
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
    show_ = session_actions.add_parser("show")
    show_.add_argument("directory", type=Path)
    dogfood_ = sub.add_parser("dogfood")
    dogfood_actions = dogfood_.add_subparsers(dest="action", required=True)
    dogfood_actions.add_parser("list")
    dogfood_prepare = dogfood_actions.add_parser("prepare")
    dogfood_prepare.add_argument("scenario")
    dogfood_prepare.add_argument("--name")
    dogfood_run = dogfood_actions.add_parser("run")
    dogfood_run.add_argument("directory", type=Path)
    dogfood_run.add_argument("--rounds", type=int, default=sessions.ROUNDS)
    dogfood_evaluate = dogfood_actions.add_parser("evaluate")
    dogfood_evaluate.add_argument("directory", type=Path)
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
                / (
                    f"{arguments.task}-claude"
                    if arguments.via == "claude"
                    else f"{arguments.task}-driver.jsonl"
                )
            )
            value = run_workflow(project, arguments.via, arguments.workflow, args, log)
        elif arguments.command == "repair-specs":
            value = repair_specs(
                arguments.project.resolve(),
                arguments.modules.split(",") if arguments.modules else None,
                arguments.task,
            )
        elif arguments.command == "grade":
            project = arguments.project.resolve()
            instance = json.loads(arguments.instance.read_text(encoding="utf-8"))
            value = grade(
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
