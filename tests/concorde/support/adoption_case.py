"""The existing-codebase case the Adoption and Scaffold tests share: a survey proposal, answers
and the runs of survey, scaffold and code_to_spec in a bound task worktree with the fake worker."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.method.scaffold.command import (
    child_metadata,
    child_reading,
    parent_reading,
)
from concorde.spec.registry import RECORD_FIELDS, registry_command, serialize
from concorde.worker_harness.runs import read_record
from tests.concorde.support.brownfield_project import BrownfieldProject
from tests.concorde.support.paths import REPOSITORY_ROOT

# A decision as the worker claims it: options named by identities, the choice by one of them.
DB_HELPER = {
    "id": "d.db-helper",
    "module": "module.shop",
    "question": "Does the shared database helper get a Module of its own?",
    "options": [
        {"id": "own-module", "text": "a Module of its own"},
        {"id": "stay-root", "text": "stay with the root"},
    ],
    "chosen": "stay-root",
    "reason": "it is two lines of connection setup",
}
# The same decision as the host records it in the output.
DB_HELPER_RECORDED = {
    "id": "d.db-helper",
    "module": "module.shop",
    "question": "Does the shared database helper get a Module of its own?",
    "options": ["a Module of its own", "stay with the root"],
    "chosen": "stay with the root",
    "reason": "it is two lines of connection setup",
    "decided_by": "worker",
}
PROPOSAL = {
    "summary": "Checkout and inventory are separate responsibilities.",
    "externals": [],
    "children": [
        {
            "id": "module.checkout",
            "title": "Checkout",
            "purpose": "Checkout turns a basket into one order.",
            "entries": ["src/checkout/"],
            "uses": [
                {
                    "target": "module.inventory",
                    "reason": "submit holds stock through inventory.stock.hold.",
                }
            ],
        },
        {
            "id": "module.inventory",
            "title": "Inventory",
            "purpose": "Inventory holds stock for baskets.",
            "entries": ["src/inventory/"],
            "uses": [],
        },
    ],
    "checks": [
        {
            "id": "check.checkout.tests",
            "module": "module.checkout",
            "argv": ["python", "-m", "pytest", "tests"],
            "timeout_seconds": 300,
            "inputs": ["src/checkout", "tests"],
            "reason": "pyproject.toml configures pytest",
        }
    ],
    "decisions": [DB_HELPER],
    "open_questions": [],
}
RETRY_QUESTION = {
    "id": "q.payment-retry",
    "module": "module.checkout",
    "subject": "retrying a declined payment",
    "observed": "a declined payment is retried once; other errors are not",
    "evidence": ["src/checkout/payment.py"],
    "why_uncertain": "nothing says whether only declines should be retried",
    "options": ["retry declines once", "retry every failure once"],
    "recommendation": "ask whether other failures should be retried",
}


def contract(path: str, identity: str) -> dict:
    text = (REPOSITORY_ROOT / path).read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        body = json.loads(fence)
        if body["id"] == identity:
            return body["schema"]
    raise AssertionError(f"{identity} not in {path}")


def register_db(root: Path) -> None:
    """Register ``module.db``, a child of the root binding ``src/db.py``, in the worktree
    ``root``, as a developer would by hand."""
    child = {
        "id": "module.db",
        "title": "Database",
        "purpose": "Database connects to the shop's store.",
        "entries": ["src/db.py"],
        "uses": [],
    }
    entry = "specs/project/db/module.md"
    (root / entry).parent.mkdir()
    (root / entry).write_text(child_reading(child, {}))
    (root / (entry + ".json")).write_text(
        json.dumps(child_metadata(child, entry), indent=2) + "\n"
    )
    parent = root / "specs/project/module.md"
    parent.write_text(parent_reading(parent.read_text(), [child]))
    value = json.loads((root / "specs/project/module.md.json").read_text())
    value["module"]["contains"].append(
        {"target": "module.db", "meaning": "#contains-db"}
    )
    (root / "specs/project/module.md.json").write_text(
        json.dumps(value, indent=2) + "\n"
    )
    registry = json.loads((root / ".concorde/specs.json").read_text())
    block = child_metadata(child, entry)["module"]
    registry["modules"].append(
        {
            "id": "module.db",
            "title": "Database",
            "entry": entry,
            **{name: block[name] for name in RECORD_FIELDS[3:]},
        }
    )
    (root / ".concorde/specs.json").write_text(serialize(registry))
    assert registry_command(root, write=True).status == "success"


class AdoptionCase(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)

    def open(self) -> Path:
        self.project.open_task()
        self.worktree = self.project.worktree()
        return self.worktree

    def survey(self, output=PROPOSAL, *extra, task=True, status="ok", error=None):
        result = {"output": output}
        if status != "ok":
            result.update(status=status, error=error)
        return self.project.run(
            "survey",
            *(("--task", "adopt") if task else ()),
            "--modules",
            "module.shop",
            "--goal",
            BrownfieldProject.plan([{"result": result}]),
            *extra,
        )

    def worker_round(self, envelope) -> dict:
        """What the run's last worker was given in its first round: its prompt, the brief its run
        directory keeps, and its tool set, from its run record (the worker's runtime directory,
        where the fake worker writes its own notes, is removed when the worker ends)."""
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        return {
            "prompt": (Path(record["run_directory"]) / "brief.md").read_text(),
            "tools": record["tools"],
        }

    def scaffolded(self) -> str:
        self.open()
        status, envelope = self.survey()
        self.assertEqual(0, status, envelope)
        status, scaffold = self.project.run(
            "scaffold", "--task", "adopt", "--input", envelope["run_id"]
        )
        self.assertEqual(0, status, scaffold)
        return envelope["run_id"]

    def describe(self, rounds, *extra, modules="module.checkout"):
        return self.project.run(
            "code_to_spec",
            "--task",
            "adopt",
            "--modules",
            modules,
            "--goal",
            BrownfieldProject.plan(rounds),
            *extra,
        )
