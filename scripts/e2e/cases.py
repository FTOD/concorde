"""SWE-bench cases: repairing an adopted case's Specs and grading a delivered change.

A case is a SWE-bench task instance: an issue of one repository at its base commit, with a test
patch and the tests that must pass once the issue is resolved. End-to-end testing prepares the
case's project at its base commit; this module repairs the Specs adoption left there in one
bounded round, and grades the merged change the way SWE-bench does, in a throwaway worktree the
project never sees.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import E2EError, run

# In a case the Specs are ours, added by adoption, and describe code we never change; so one
# round of repairing their review findings precedes the issue. This exception to "review gaps
# wait for a person" holds for end-to-end cases only, which is why it lives here.
REPAIR_INTENT = (
    "Repair every blocking finding of the Spec panel given as input, in the documents of the "
    "Modules it names. These Specs describe the project's existing code, which you cannot read: "
    "change what the Specs say, never the code, and change only what the findings and the "
    "existing Specs justify. Where a repair would need a fact about the code that they do not "
    "state, or a decision about intended behaviour, write an open question instead of a promise."
)


# The execution commands, which run as ``concorde <command>``; every other name is an Operation.
COMMANDS = ("task-validation", "delivery", "scaffold")


def concorde_run(concorde: str, worktree: Path, argv: list[str]) -> dict:
    """One Operation or execution command run in ``worktree``, whose workspace binding it works
    on; its result, whatever its exit status."""
    prefix = [] if argv[0] in COMMANDS else ["run"]
    done = subprocess.run(
        [concorde, *prefix, *argv],
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
            f"`concorde {' '.join(prefix + argv)}` in {worktree} printed no JSON result "
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
    worktree = Path(opened["record"]["worktree"])
    steps: list[dict] = []

    def step(name: str, argv: list[str]) -> dict | None:
        result = run_operation(concorde, worktree, argv)
        steps.append({"step": name, **_brief(result)})
        return result if result.get("status") == "ok" else None

    def stopped(name: str) -> dict:
        return {"task": task, "modules": modules, "steps": steps, "stopped_at": name}

    review = step("spec_panel", ["spec_panel", "--modules", bound])
    if review is None:
        return stopped("spec_panel")
    if (review.get("output") or {}).get("verdict") != "accepted":
        if (
            step(
                "specify",
                [
                    "specify",
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
        if step("spec_panel_again", ["spec_panel", "--modules", bound]) is None:
            return stopped("spec_panel_again")
    for name in ("task-validation", "delivery"):
        if step(name, [name]) is None:
            return stopped(name)
    run([concorde, "task", "merge", task], cwd=project)
    return {"task": task, "modules": modules, "steps": steps, "stopped_at": None}


# The header lines of a Git patch that name the path a change comes from: the old side of a
# content change, with its ``a/`` prefix, and the source of a rename or copy. Git quotes a path
# with special characters and ends a ``---`` line with a tab when its path holds a space.
SOURCE_LINE = re.compile(r"^(--- |rename from |copy from )(.+?)\t?$")
QUOTED_ESCAPES = {
    "a": 7,
    "b": 8,
    "f": 12,
    "n": 10,
    "r": 13,
    "t": 9,
    "v": 11,
    '"': 34,
    "\\": 92,
}


def unquote(text: str) -> str:
    """A path as Git writes it in a patch: as is, or between double quotes with C escapes and
    octal bytes."""
    if not (len(text) >= 2 and text[0] == text[-1] == '"'):
        return text
    raw = bytearray()
    body = text[1:-1]
    index = 0
    while index < len(body):
        char = body[index]
        if char != "\\":
            raw += char.encode("utf-8")
            index += 1
        elif (
            body[index + 1 : index + 4].isdigit()
            and len(body[index + 1 : index + 4]) == 3
        ):
            raw.append(int(body[index + 1 : index + 4], 8))
            index += 4
        else:
            raw.append(QUOTED_ESCAPES.get(body[index + 1 : index + 2], ord("\\")))
            index += 2
    return raw.decode("utf-8", errors="surrogateescape")


def patched_paths(tree: Path, patch: Path) -> list[str]:
    """Every path ``patch`` touches, on either side: Git's own reading of the patch gives each
    changed file's path, whatever characters it holds, and the patch's source lines add the paths
    that renames and copies come from."""
    listed = run(["git", "apply", "--numstat", "-z", str(patch)], cwd=tree).stdout
    paths = {
        entry.split("\t", 2)[2]
        for entry in listed.split("\0")
        if entry.count("\t") >= 2 and entry.split("\t", 2)[2]
    }
    header = False
    for line in patch.read_text(encoding="utf-8").split("\n"):
        # Only a file's header names paths; a hunk's removed line may begin with ``---`` too.
        if line.startswith("diff --git "):
            header = True
        elif line.startswith("@@"):
            header = False
        found = SOURCE_LINE.match(line) if header else None
        if found is None:
            continue
        kind, path = found.group(1), unquote(found.group(2))
        if path == "/dev/null":
            continue
        paths.add(path[2:] if kind == "--- " and path.startswith("a/") else path)
    return sorted(paths)


def reset_patched_files(tree: Path, patch: Path, base: str) -> list[str]:
    """Put every file ``patch`` touches back as it was at ``base``, removing the ones ``base``
    lacks, as SWE-bench does before it applies a test patch: the change under test may have
    edited the same test files, and the case's tests are graded as the case wrote them."""
    paths = patched_paths(tree, patch)
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


# A pytest plugin that records every test's status under its complete node identity as one
# JSON line per report, written as it goes: pytest's short summary cuts an identity at its first
# space and names no test on a SKIPPED line, so statuses are never read from it.
REPORT_PLUGIN = "concorde_grade_report"
REPORT_VARIABLE = "CONCORDE_GRADE_REPORT"
REPORT_PLUGIN_SOURCE = """\
import json
import os


def _write(nodeid, status):
    with open(os.environ["CONCORDE_GRADE_REPORT"], "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"test": nodeid, "status": status}) + "\\n")


def pytest_runtest_logreport(report):
    expected = hasattr(report, "wasxfail")
    if report.when == "call":
        if report.passed:
            _write(report.nodeid, "XPASS" if expected else "PASSED")
        elif report.failed:
            _write(report.nodeid, "FAILED")
        else:
            _write(report.nodeid, "XFAIL" if expected else "SKIPPED")
    elif report.failed:
        _write(report.nodeid, "ERROR")
    elif report.skipped and report.when == "setup":
        _write(report.nodeid, "XFAIL" if expected else "SKIPPED")


def pytest_collectreport(report):
    if report.failed:
        _write(report.nodeid, "ERROR")
"""

# How SWE-bench grades a listed test's status (references/swe-bench/swebench/harness/
# grading.py): an expected failure counts as passed, and a skipped PASS_TO_PASS test is no
# regression, while a skipped FAIL_TO_PASS test is no resolution.
PASSING = ("PASSED", "XFAIL")
MAINTAINED = ("PASSED", "XFAIL", "SKIPPED")


def read_report(path: Path) -> dict[str, str]:
    """Each test's status from the plugin's report; a later report of a test (its teardown's
    error) replaces an earlier one, as the later summary line does in SWE-bench's parser."""
    statuses: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except OSError:
        return statuses
    for line in lines:
        if line.strip():
            entry = json.loads(line)
            statuses[entry["test"]] = entry["status"]
    return statuses


def status_of(test: str, statuses: dict[str, str]) -> str:
    """The status of a listed test. Like SWE-bench, a listed identity cut inside its parameters
    (more ``[`` than ``]``, as SWE-bench's datasets cut identities at their first space) stands
    for the tests it begins when they agree on passing or not; otherwise it was ``not run``."""
    if test in statuses:
        return statuses[test]
    if test.count("[") > test.count("]"):
        matches = [statuses[name] for name in statuses if name.startswith(test)]
        if matches and len({status in PASSING for status in matches}) == 1:
            return matches[0]
    return "not run"


def case_tests(instance: dict, field: str) -> list[str]:
    value = instance.get(field) or []
    return json.loads(value) if isinstance(value, str) else list(value)


# The longest a case's test run may take before grading gives up on it, in seconds.
GRADE_TIMEOUT = 1800


def _text(output: str | bytes | None) -> str:
    """A timed-out process's captured output, which may be bytes even with ``text=True``."""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output or ""


def _keep(log: Path | None, output: str) -> Path | None:
    """Write the test run's whole output to ``log``, when the caller names one."""
    if log is None:
        return None
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output, encoding="utf-8")
    return log


def remove_grading_worktree(project: Path, tree: Path, scratch: Path) -> list[str]:
    """Remove the grading worktree ``tree``, its registration in ``project`` and the scratch
    directory that holds it; what is left of them, each with Git's account, empty when nothing
    is."""
    removal = subprocess.run(
        ["git", "worktree", "remove", "--force", str(tree)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    shutil.rmtree(scratch, ignore_errors=True)
    # A registration whose directory is gone, as after a failed removal, is pruned.
    subprocess.run(
        ["git", "worktree", "prune"], cwd=project, capture_output=True, check=False
    )
    listed = subprocess.run(
        ["git", "worktree", "list", "--porcelain", "-z"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    left = []
    if listed.returncode != 0:
        left.append(
            f"`git worktree list` exited with status {listed.returncode}: "
            f"{listed.stderr.strip()}"
        )
    elif {f"worktree {tree}", f"worktree {os.path.realpath(tree)}"} & set(
        listed.stdout.split("\0")
    ):
        left.append(f"{tree} is still registered as a worktree of {project}")
    if scratch.exists():
        left.append(f"the directory {scratch} still exists")
    if left and removal.returncode != 0:
        left.append(
            f"`git worktree remove --force` exited with status {removal.returncode}: "
            f"{removal.stderr.strip()}"
        )
    return left


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
    # The worktree's whole life, from its creation, lies inside one cleanup: however grading
    # ends, the worktree is removed, or the grading fails with what is left of it.
    failure: BaseException | None = None
    try:
        run(["git", "worktree", "add", "-q", "--detach", str(tree), ref], cwd=project)
        patch = scratch / "test.patch"
        patch.write_text(instance["test_patch"], encoding="utf-8")
        reset_patched_files(tree, patch, instance["base_commit"])
        run(["git", "apply", str(patch)], cwd=tree)
        files = sorted({test.split("::")[0] for test in fail_to_pass + pass_to_pass})
        plugin = scratch / "plugin"
        plugin.mkdir()
        (plugin / f"{REPORT_PLUGIN}.py").write_text(
            REPORT_PLUGIN_SOURCE, encoding="utf-8"
        )
        report = scratch / "report.jsonl"
        # The worktree's --pythonpath directories go first, the caller's own entries after them
        # and the report plugin last, so that it shadows nothing of the project's.
        inherited = os.environ.get("PYTHONPATH")
        environment = {
            **os.environ,
            REPORT_VARIABLE: str(report),
            "PYTHONPATH": os.pathsep.join(
                [
                    *(str(tree / item) for item in pythonpath),
                    *([inherited] if inherited else []),
                    str(plugin),
                ]
            ),
        }
        # Colour is off whatever the caller's environment asks for (FORCE_COLOR would otherwise
        # wrap every status of the kept output in escapes).
        command = [
            str(python),
            "-m",
            "pytest",
            "-rA",
            "--color=no",
            "-p",
            "no:cacheprovider",
            "-p",
            REPORT_PLUGIN,
            *files,
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=tree,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=GRADE_TIMEOUT,
            )
        except subprocess.TimeoutExpired as error:
            stdout, stderr = _text(error.stdout), _text(error.stderr)
            kept = _keep(log, stdout + "\n" + stderr)
            raise E2EError(
                "grade_timeout",
                f"the tests of case {instance.get('instance_id')} on {ref} did not finish "
                f"within the grading limit of {GRADE_TIMEOUT} seconds: `{' '.join(command)}` "
                f"in the grading worktree {tree} was stopped"
                + (f"; its whole output is kept in {kept}" if kept else ""),
                stdout=stdout[-3000:],
                stderr=stderr[-3000:],
                **({"log": str(kept)} if kept else {}),
            ) from error
        statuses = read_report(report)
    except BaseException as error:
        failure = error
        raise
    finally:
        left = remove_grading_worktree(project, tree, scratch)
        if left:
            cause = (
                f"; grading had failed before: {failure.code}: {failure.detail}"
                if isinstance(failure, E2EError)
                else f"; grading had failed before: {failure!r}"
                if failure is not None
                else ""
            )
            raise E2EError(
                "cleanup_failed",
                f"the grading worktree {tree} of case {instance.get('instance_id')} could not "
                f"be removed: {'; '.join(left)}{cause}",
                worktree=str(tree),
                left=left,
                **(
                    {"cause": failure.evidence | {"code": failure.code}}
                    if isinstance(failure, E2EError)
                    else {}
                ),
            ) from failure
    _keep(log, completed.stdout + "\n" + completed.stderr)

    def split(tests: list[str], counted: tuple[str, ...]) -> dict:
        found = {test: status_of(test, statuses) for test in tests}
        return {
            "passed": sum(status in counted for status in found.values()),
            "total": len(tests),
            "not_passed": {
                test: status for test, status in found.items() if status not in counted
            },
        }

    f2p, p2p = split(fail_to_pass, PASSING), split(pass_to_pass, MAINTAINED)
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
