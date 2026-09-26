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
