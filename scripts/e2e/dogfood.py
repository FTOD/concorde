"""Dogfood scenarios: a known Concorde defect, a develop install and a real session that must find it.

A scenario (``scenarios/<name>.json`` beside this file) names a project, a fault, the prompt a
developer gives the main agent and what the session must achieve. ``prepare`` clones this
checkout's committed Concorde into a scenario directory, ``test-<name>`` of the end-to-end root,
injects the fault there as a commit of its own, builds it, clones the project, makes a develop
install of it from the faulty clone, writes the project's worker configuration and records the
baselines. ``run`` drives a headless session in the
project with the scenario's prompt; ``evaluate`` then decides, from files alone, whether the
session left Concorde untouched, wrote defect reports that pass ``issues report --check`` and are
accepted by a clone of the Concorde repository, classified the defect as expected and did not work
around it.

Nothing here touches the checkout itself: the fault lives only in the scenario's clone.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import sessions
from common import (
    CHECKOUT,
    E2EError,
    clone,
    fresh_directory,
    repository_url,
    run,
    taken,
    test_directory,
)

SCENARIOS = Path(__file__).resolve().parent / "scenarios"
FIELDS = ("name", "description", "project", "fault", "prompt", "expect")
# The installed framework parts whose bytes a session must leave as they were.
FRAMEWORK_PARTS = ("src", "scripts", "prompts", "generated")
GIT = ["git", "-c", "user.name=e2e", "-c", "user.email=e2e@example.com"]
WORKERS = ".concorde/workers.json"
RECEIPT = ".concorde/install.json"


def scenario(name: str) -> dict:
    """A scenario by name, every field of the shape it needs: ``unknown_scenario`` naming the
    known ones when no file names it, ``invalid_scenario`` naming the file and the field when its
    file is no valid scenario."""
    known = sorted(item.stem for item in SCENARIOS.glob("*.json"))
    if name not in known:
        raise E2EError(
            "unknown_scenario",
            f"no scenario is named {name!r}; known: {', '.join(known) or 'none'}",
        )
    path = SCENARIOS / f"{name}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise E2EError(
            "invalid_scenario", f"{path} cannot be read as JSON ({error})"
        ) from error
    problem = scenario_problem(name, value)
    if problem:
        raise E2EError("invalid_scenario", f"{path}: {problem}")
    return value


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _texts(value, empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (empty or bool(value))
        and all(_text(item) for item in value)
    )


def scenario_problem(name: str, value) -> str | None:
    """What makes ``value`` no valid scenario of the file ``name``, or None."""
    if not isinstance(value, dict):
        return f"it holds a JSON {type(value).__name__}, not an object"
    missing = [field for field in FIELDS if field not in value]
    if missing:
        return f"it lacks the field(s) {', '.join(missing)}"
    if value["name"] != name:
        return f"its name {value['name']!r} is not its file's name {name!r}"
    for field in ("description", "prompt"):
        if not _text(value[field]):
            return f"its {field} is no text"
    project = value["project"]
    if not isinstance(project, dict) or not all(
        _text(project.get(key)) for key in ("repository", "rev")
    ):
        return "its project is no object with the texts repository and rev"
    fault = value["fault"]
    if not isinstance(fault, dict) or not _text(fault.get("summary")):
        return "its fault is no object with the text summary"
    edits = fault.get("edits")
    if not isinstance(edits, list) or not edits:
        return "its fault's edits are no non-empty list"
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict) or not (
            _text(edit.get("file"))
            and _text(edit.get("old"))
            and isinstance(edit.get("new"), str)
        ):
            return (
                f"edit {index} of its fault is no object with file, old and new texts"
            )
        if edit["old"] in edit["new"]:
            # The old text would survive the injection, which could then be repeated.
            return f"edit {index} of its fault keeps its old text in its new text"
    expect = value["expect"]
    if not isinstance(expect, dict):
        return "its expect is no object"
    if not _texts(expect.get("types"), empty=False):
        return "its expect's types are no non-empty list of texts"
    for key in ("basis", "unchanged"):
        if not _texts(expect.get(key)):
            return f"its expect's {key} is no list of texts"
    return None


def listing() -> list[dict]:
    return [
        {"name": item.stem, "description": scenario(item.stem)["description"]}
        for item in sorted(SCENARIOS.glob("*.json"))
    ]


def inject(concorde: Path, fault: dict) -> str:
    """Apply the fault's edits to the Concorde clone, commit them and return the commit."""
    for index, edit in enumerate(fault["edits"]):
        path = concorde / edit["file"]
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        count = text.count(edit["old"])
        if count != 1:
            raise E2EError(
                "fault_not_applicable",
                f"edit {index} of the fault finds its old text {count} time(s) in "
                f"{edit['file']} instead of once; the Concorde source changed since the "
                "scenario was written, so update the scenario's fault",
            )
        path.write_text(text.replace(edit["old"], edit["new"]), encoding="utf-8")
    run([*GIT, "commit", "-qam", f"Inject fault: {fault['summary']}"], cwd=concorde)
    return run(["git", "rev-parse", "HEAD"], cwd=concorde).stdout.strip()


def framework_digest(project: Path) -> str:
    """The digest of the installed framework's sources, leaving out Python's caches."""
    digest = hashlib.sha256()
    framework = project / ".concorde/framework"
    for part in FRAMEWORK_PARTS:
        for path in sorted((framework / part).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(framework).as_posix().encode() + b"\0")
                digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def receipt_digest(project: Path) -> str | None:
    """The digest of the install receipt's bytes, or None when it cannot be read."""
    try:
        return "sha256:" + hashlib.sha256((project / RECEIPT).read_bytes()).hexdigest()
    except OSError:
        return None


def installed_digests(project: Path) -> dict:
    """The digest of each file the install receipt names outside ``.concorde/``;
    ``receipt_unreadable`` when the receipt cannot be read as one naming its files."""
    path = project / RECEIPT
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise ValueError(f"it holds a JSON {type(receipt).__name__}, not an object")
        files = receipt.get("files")
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            raise ValueError("its files are not a list of paths")
    except (OSError, ValueError) as error:
        raise E2EError(
            "receipt_unreadable",
            f"the install receipt {path} cannot be read as the list of installed files "
            f"({error})",
        ) from error
    return {
        path: "sha256:" + hashlib.sha256((project / path).read_bytes()).hexdigest()
        for path in sorted(files)
        if not path.startswith(".concorde/") and (project / path).is_file()
    }


def install_command(concorde: Path, project: Path) -> list[str]:
    """The develop install of the project from the faulty clone."""
    return [
        sys.executable,
        str(concorde / "scripts/install-concorde.py"),
        str(project),
        "--develop",
        "--without-d2",
    ]


def prepare(
    name: str,
    root: Path,
    workers: dict,
    directory: str | None = None,
) -> dict:
    """Set a scenario up under ``root``: the faulty Concorde clone and the project, with
    ``workers`` as the project's worker configuration."""
    chosen = scenario(name)
    base = test_directory(root, name if directory is None else directory)
    if taken(base):
        raise E2EError(
            "scenario_exists",
            f"{base} already exists; remove it or pass another --name",
        )
    base.mkdir(parents=True)
    concorde, project = base / "concorde", base / "project"
    run(["git", "clone", "-q", str(CHECKOUT), str(concorde)], cwd=base)
    fault = inject(concorde, chosen["fault"])
    run([sys.executable, "scripts/concorde.py", "build"], cwd=concorde)
    clone(
        repository_url(chosen["project"]["repository"]),
        chosen["project"]["rev"],
        project,
    )
    run(install_command(concorde, project), cwd=concorde)
    command = str(project / ".concorde/bin/concorde")
    proposed = json.loads(
        run([command, "init", "--propose", "--name", project.name], cwd=project).stdout
    )
    proposal = base / "proposal.json"
    proposal.write_text(json.dumps(proposed["result"]))
    run([command, "init", "--apply", "--proposal", str(proposal)], cwd=project)
    proposal.unlink()
    # No command writes the worker configuration: a developer writes it by hand, as here.
    (project / WORKERS).write_text(json.dumps(workers, indent=2) + "\n")
    run(["git", "add", "-A"], cwd=project)
    run([*GIT, "commit", "-qm", "Adopt Concorde (develop install)"], cwd=project)
    record = {
        "scenario": name,
        "worker_models": sorted(workers.get("enabled_models", {})),
        "concorde": str(concorde),
        "fault_commit": fault,
        "project": str(project),
        "project_head": run(["git", "rev-parse", "HEAD"], cwd=project).stdout.strip(),
        "framework": framework_digest(project),
        "receipt": receipt_digest(project),
        "installed": installed_digests(project),
        "unchanged": {
            path: run(["git", "rev-parse", f"HEAD:{path}"], cwd=project).stdout.strip()
            for path in chosen["expect"].get("unchanged", [])
        },
    }
    (base / "dogfood.json").write_text(json.dumps(record, indent=2) + "\n")
    return {"directory": str(base), **record}


def _record(base: Path) -> dict:
    try:
        return json.loads((base / "dogfood.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise E2EError(
            "not_prepared",
            f"{base} holds no readable dogfood.json ({error}); run `dogfood prepare` first",
        ) from error


def run_scenario(base: Path, rounds: int = sessions.ROUNDS) -> dict:
    """Drive the scenario's session to its end, then evaluate it."""
    record = _record(base)
    chosen = scenario(record["scenario"])
    # Each run keeps its own session, even beside one started in the same second.
    directory = fresh_directory(base / "sessions")
    session = sessions.start(
        Path(record["project"]),
        chosen["prompt"],
        directory,
        rounds=rounds,
    )
    return {"session": session, "evaluation": evaluate(base)}


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"check": name, "passed": passed, "detail": detail}


def _untouched(record: dict) -> dict:
    concorde, project = Path(record["concorde"]), Path(record["project"])
    problems = []
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=concorde, capture_output=True, text=True
    ).stdout.strip()
    if head != record["fault_commit"]:
        problems.append(
            f"the Concorde clone moved from {record['fault_commit']} to {head}"
        )
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=concorde, capture_output=True, text=True
    ).stdout.split("\n")
    changed = [line for line in dirty if line.strip()]
    if changed:
        problems.append(f"the Concorde clone has changes: {', '.join(changed[:10])}")
    if framework_digest(project) != record["framework"]:
        problems.append("the installed framework under .concorde/framework changed")
    if receipt_digest(project) != record["receipt"]:
        problems.append(f"the install receipt {project / RECEIPT} changed")
    try:
        now = installed_digests(project)
    except E2EError as error:
        # A session that tampered with the install receipt touched Concorde: no error, a finding.
        problems.append(error.detail)
    else:
        problems += [
            f"the installed file {path} changed"
            for path, value in record["installed"].items()
            if now.get(path) != value
        ]
    return _check(
        "concorde_untouched",
        not problems,
        "; ".join(problems)
        or "the Concorde clone, the framework copy, the install receipt and every installed file "
        "are as installed",
    )


def refusal(done: subprocess.CompletedProcess) -> str:
    """The whole text of a command's refusal: its standard output and its standard error."""
    text = "\n".join(
        part for part in (done.stdout.strip(), done.stderr.strip()) if part
    )
    return text or f"exit status {done.returncode} without output"


def _reports(project: Path) -> list[Path]:
    return sorted((project / ".concorde/runs/defects").glob("*.json"))


def _checked(project: Path, reports: list[Path]) -> dict:
    refused = []
    command = project / ".concorde/bin/concorde"
    for path in reports:
        try:
            done = subprocess.run(
                [str(command), "issues", "report", "--check", "--file", str(path)],
                cwd=project,
                capture_output=True,
                text=True,
            )
        except OSError as error:
            raise E2EError(
                "command_failed",
                f"the project's installed command {command} could not be started to check "
                f"{path.name}: {error}",
            ) from error
        if done.returncode != 0:
            refused.append(f"{path.name}: {refusal(done)}")
    return _check(
        "reports_checked",
        bool(reports) and not refused,
        "; ".join(refused)
        or (
            f"{len(reports)} report(s) pass issues report --check"
            if reports
            else "no report"
        ),
    )


def _accepted(concorde: Path, reports: list[Path]) -> dict:
    """Record every report into a throwaway clone of the Concorde repository, as its session
    would, so the check covers what the receiving side refuses."""
    refused = []
    with tempfile.TemporaryDirectory() as scratch:
        intake = Path(scratch) / "concorde"
        run(["git", "clone", "-q", str(concorde), str(intake)], cwd=Path(scratch))
        for path in reports:
            done = subprocess.run(
                [
                    sys.executable,
                    "scripts/issues.py",
                    "report",
                    "--file",
                    str(path),
                    "--root",
                    str(intake),
                ],
                cwd=intake,
                capture_output=True,
                text=True,
            )
            if done.returncode != 0:
                refused.append(f"{path.name}: {refusal(done)}")
    return _check(
        "reports_accepted",
        bool(reports) and not refused,
        "; ".join(refused)
        or (
            f"{len(reports)} report(s) recorded by a clone of the Concorde repository"
            if reports
            else "no report"
        ),
    )


def matches(report: dict, expect: dict) -> bool:
    """Whether a report classifies the defect the way the scenario expects."""
    basis = str(report.get("basis") or "").lower()
    return report.get("type") in expect.get("types", [report.get("type")]) and all(
        phrase.lower() in basis for phrase in expect.get("basis", [])
    )


def _classified(reports: list[Path], expect: dict) -> dict:
    found = []
    for path in reports:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(value, dict) and matches(value, expect):
            found.append(path.name)
    return _check(
        "classified",
        bool(found),
        f"matching: {', '.join(found)}"
        if found
        else f"no report is of type {expect.get('types')} with a basis naming "
        f"{expect.get('basis')}",
    )


def unchanged(project: Path, expected: dict) -> list[str]:
    """Each place where a path the session must not change differs from its recorded blob: any
    branch, and the working tree of any worktree."""
    problems = []
    branches = run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"], cwd=project
    ).stdout.split()
    trees = [
        line.split(" ", 1)[1]
        for line in run(
            ["git", "worktree", "list", "--porcelain"], cwd=project
        ).stdout.splitlines()
        if line.startswith("worktree ")
    ]
    for path, blob in expected.items():
        for branch in branches:
            found = subprocess.run(
                ["git", "rev-parse", f"{branch}:{path}"],
                cwd=project,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if found != blob:
                problems.append(f"{path} differs on branch {branch}")
        for tree in trees:
            file = Path(tree) / path
            found = (
                run(["git", "hash-object", str(file)], cwd=project).stdout.strip()
                if file.is_file()
                else ""
            )
            if found != blob:
                problems.append(f"{path} differs in the worktree {tree}")
    return problems


def evaluate(base: Path) -> dict:
    """Whether the session left Concorde alone and reported the defect well, check by check."""
    record = _record(base)
    chosen = scenario(record["scenario"])
    project = Path(record["project"])
    reports = _reports(project)
    problems = unchanged(project, record["unchanged"])
    checks = [
        _untouched(record),
        _checked(project, reports),
        _accepted(Path(record["concorde"]), reports),
        _classified(reports, chosen["expect"]),
        _check(
            "no_workaround",
            not problems,
            "; ".join(problems)
            or f"{', '.join(record['unchanged']) or 'nothing'} unchanged everywhere",
        ),
    ]
    result = {
        "scenario": record["scenario"],
        "passed": all(item["passed"] for item in checks),
        "reports": [path.name for path in reports],
        "checks": checks,
    }
    (base / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
