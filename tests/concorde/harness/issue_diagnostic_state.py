"""Source-owned disposable Issue diagnostic fixture; recovered setup, no model calls."""

import hashlib
import json
import os
import pathlib

from concorde.delivery.records import receipt
from concorde.harness.change_worktree import read_change
from concorde.issue_solving.records import solutions
from concorde.validation.records import validated_tree
from concorde.issues.store import read_issue, resolve_report

S = pathlib.Path(os.environ["S"])
f = json.loads((S / "fixture.json").read_text())
r = pathlib.Path(f["root"])
p = pathlib.Path(f["primary"])
o = json.loads((S / "summary.json").read_text())
state = read_change(r)
record, revision = read_issue(r, f["receipt"]["issue_id"])
resolve_report(r, f["receipt"])
assert record["reports"] == f["before_reports"]
unchanged = all(
    hashlib.sha256((r / x).read_bytes()).hexdigest() == d
    for x, d in f["input_digests"].items()
)
o["persistence"] = {
    "change": f["change_id"],
    "issue": f["receipt"]["issue_id"],
    "report": f["receipt"]["report_id"],
    "issueStatus": record["status"],
    "disposition": record["dispositions"][-1]["reason"]
    if record["dispositions"]
    else None,
    "reportsImmutable": True,
    "specCodeConfigUnchanged": unchanged,
    "status": state["status"],
    "phase": state["phase"],
    "validatedTree": validated_tree(state),
    "candidateStatusExists": (r / ".concorde/status").exists(),
    "candidateRunsExists": (r / ".concorde/runs").exists(),
    "primaryStatusExists": (p / f".concorde/status/{f['change_id']}.json").exists(),
    "nativeIssueArchives": len(
        list((p / ".concorde/runs").glob("*/native-issue.json"))
    ),
    "delivered": bool(receipt(state)),
}
solution = solutions(state).get(f["receipt"]["issue_id"], {})
o["persistence"].update(
    attempts=solution.get("attempts", 0),
    acceptedDecisions=len(solution.get("history", [])),
    verificationDigests=len(solution.get("verification", [])),
    pendingJournal=bool(solution.get("pending_disposition")),
)
print(json.dumps(o["persistence"]))
