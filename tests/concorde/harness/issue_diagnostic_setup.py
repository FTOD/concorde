"""Source-owned disposable Issue diagnostic fixture; recovered setup, no model calls."""

import hashlib
import json
import os
import pathlib
import runpy
import subprocess

from concorde.distribution.project_defaults import install_project_defaults
from concorde.harness.change_worktree import bind_owner, ensure_change, read_change
from concorde.issues.store import read_issue, report_issue
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository

C = pathlib.Path(os.environ["C"])
S = pathlib.Path(os.environ["S"])
mode = "A"
r = S / "primary"
r.mkdir(parents=True)
config = typed(
    "concorde-operation-configuration",
    dict(
        model=os.environ["CONCORDE_DIAGNOSTIC_MODEL"],
        thinking="medium",
        timeout_seconds=240,
    ),
)
install_project_defaults(r, C)
apply_project_proposal(
    r, C, project_proposal(r, C, "Increment", config, "module.increment")
)
entry = """# Integer increment

## Purpose

Supply Python callers with the next integer. This pure arithmetic Module has no persistence, network, command or configuration responsibilities.

## Terminology

| Term | Definition |
| --- | --- |
| Supported integer | A Python int excluding bool, with no magnitude bound. |

<a id="concept.increment.supported-integer"></a>

A supported integer is any Python int that is not a bool.

## Usage

Import increment from app.increment and call increment(n) with any supported integer n. The return is n + 1, including negative and arbitrarily large integers. For example increment(0) returns 1. Inputs outside this domain have no supported behavior and callers must not supply them. Calls do not mutate input or external state. Repetition returns the same result. Calls are synchronous; there is no cancellation protocol, retry or durable state.

## Design

The Increment function performs one integer addition. The Check compares its return against arithmetic expectations at zero, negative, positive and large values. This requires no external collaborator. There are no imported terminology restatements.

<a id="realization.increment.function"></a>
The Increment function computes the result without external effects.

<a id="realization.increment.check"></a>
The Check independently exercises the stated cases.

## Relationships

The Check invokes the Increment function to test the contract; neither has another provider or child.

```mermaid
flowchart LR
 accTitle: Increment verification
 accDescr: Check exercises the pure increment function.
 check["Check"] -->|checks| function["Increment function"]
```
"""
precise = """# Increment obligations

## Requirements

### req.increment.result — Next integer

increment SHALL return n + 1 for every supported integer n.

### req.increment.effects — Pure arithmetic

increment SHALL have no externally observable side effects.

## Scenarios

### scenario.increment.values — Integer results

- GIVEN n is each of -5, 0, 9 and 10**100
- WHEN increment(n) is called twice
- THEN both calls return n + 1
- AND there is no output or external state change
"""
for path in ("specs/project/module.md", "specs/project/module.md.json"):
    (r / path).unlink()
(r / "specs/project").rmdir()
owns = ["specs/increment/module.md", "specs/increment/obligations.md"]
for name, body, role in [
    ("module", entry, "module"),
    ("obligations", precise, "implementation"),
]:
    p = r / f"specs/increment/{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    m = dict(
        schema_version=3,
        document=dict(
            id=f"document.increment.{name}", owner="module.increment", role=role
        ),
        defines=[],
        relations=[],
    )
    if name == "module":
        m["module"] = dict(
            title="Increment",
            owns=owns,
            contains=[],
            uses=[],
            includes=[],
            participates=[],
        )
        m["defines"] = [
            dict(
                id="concept.increment.supported-integer",
                type="concept",
                title="Supported integer",
                meaning="#concept.increment.supported-integer",
            ),
            dict(
                id="realization.increment.function",
                type="realization",
                title="Increment function",
                meaning="#realization.increment.function",
                entries=["app/increment.py"],
            ),
            dict(
                id="realization.increment.check",
                type="realization",
                title="Check",
                meaning="#realization.increment.check",
                entries=["checks/increment_check.py"],
            ),
        ]
        m["relations"] = [
            dict(
                type="relates",
                source="realization.increment.check",
                verb="checks",
                target="realization.increment.function",
            )
        ]
    pathlib.Path(str(p) + ".json").write_text(json.dumps(m))
(r / ".concorde/specs.json").write_text(
    json.dumps(
        dict(
            schema_version=3,
            modules=[
                dict(
                    id="module.increment",
                    title="Increment",
                    entry="specs/increment/module.md",
                    owns=owns,
                    contains=[],
                    uses=[],
                    includes=[],
                    participates=[],
                )
            ],
        )
    )
)
configuration = json.loads((r / ".concorde/config.json").read_text())
configuration["checks"] = [
    dict(
        id="check.increment",
        module="module.increment",
        argv=["{python}", "checks/increment_check.py"],
        timeout_seconds=30,
        inputs=["app/increment.py", "checks/increment_check.py"],
    )
]
(r / ".concorde/config.json").write_text(json.dumps(configuration, indent=2))
(r / "app").mkdir()
(r / "checks").mkdir()
(r / "app/increment.py").write_text("def increment(n):\n    return n - 1\n")
(r / "checks/increment_check.py").write_text("""import sys,io,contextlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.increment import increment
# Verifies scenario.increment.values
out=io.StringIO()
with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):
 for n in (-5,0,9,10**100):
  assert increment(n)==n+1
  assert increment(n)==n+1
assert not out.getvalue()
""")


def git(*a):
    subprocess.run(["git", *a], cwd=r, check=True, capture_output=True)


git("init", "-q")
git("config", "user.name", "Fixture")
git("config", "user.email", "fixture@example.invalid")
git("add", ".")
git("commit", "-qm", "Historical defective arithmetic")
git("worktree", "add", "-b", "fix", str(S / "candidate"))
r = S / "candidate"
task = dict(target_id="module.increment", task="Resolve selected Issue")
ensure_change(r, task=task)
bind_owner(r, task)
assert runpy.run_path(str(r / "app/increment.py"))["increment"](0) == -1
message = (
    "Observed increment(0) returned -1, violating req.increment.result (expected 1). "
)
message += (
    "The caller has since replaced subtraction with addition and run the configured check successfully. Independently verify the current fix before resolution, not just trust this report."
    if mode == "A"
    else "This bug is still present: no caller repair has been made. The implementation needs to return the next integer rather than the previous one. Return the necessary code-repair intent to the caller; do not pretend it is fixed."
)
receipt = report_issue(
    r,
    dict(
        report_key="observed-wrong-result",
        type="bug",
        subtype=None,
        title="Increment subtracts instead of adds",
        description=message,
        impact="Every supported integer receives the wrong next value.",
        basis="req.increment.result and scenario.increment.values",
        owner_target_id="module.increment",
        evidence=[
            dict(
                path="app/increment.py",
                description="Observed subtraction, not increment",
            )
        ],
    ),
    dict(
        invocation_id="independent-fixture-observation-" + mode,
        agent="host",
        operation="concorde-issues",
        phase="report",
        target_id="module.increment",
        context_id="sha256:" + "a" * 64,
        change_id=None,
        head=None,
    ),
)
if mode == "A":
    (r / "app/increment.py").write_text("def increment(n):\n    return n + 1\n")
    subprocess.run(
        [str(C / ".venv/bin/python"), "checks/increment_check.py"],
        cwd=r,
        check=True,
        capture_output=True,
    )
v = validate_repository(r, package_root=C)
assert v.status == "success", [(x.rule_id, x.message) for x in v.findings]
record, rev = read_issue(r, receipt["issue_id"])
state = read_change(r)

paths = [
    ".concorde/specs.json",
    ".concorde/config.json",
    "specs/increment/module.md",
    "specs/increment/module.md.json",
    "specs/increment/obligations.md",
    "specs/increment/obligations.md.json",
    "app/increment.py",
    "checks/increment_check.py",
]
digests = {x: hashlib.sha256((r / x).read_bytes()).hexdigest() for x in paths}
(S / "fixture.json").write_text(
    json.dumps(
        dict(
            root=str(r),
            primary=str(S / "primary"),
            receipt=receipt,
            revision=rev,
            change_id=state["change_id"],
            before_reports=record["reports"],
            input_digests=digests,
        )
    )
)
