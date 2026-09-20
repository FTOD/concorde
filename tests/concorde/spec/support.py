"""Consumer fixture and explicit Pi worker double for the Profile 15 boundary."""

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path

from concorde.distribution.project_defaults import install_project_defaults
from concorde.harness.pi_rpc import PiRun
from concorde.harness.pi_worker import WorkerResult
from concorde.harness.worker_executor import WorkerExecutor, WorkerOutcome
from concorde.harness.worker_profile import external_worker_name, worker_profile
from concorde.spec.initialize import (
    apply_project_proposal,
    empty_target,
    project_proposal,
)
from concorde.spec.typed_data import typed

PACKAGE = Path(__file__).resolve().parents[3]
CONFIGURATION = typed(
    "concorde-operation-configuration",
    {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
)
USAGE = {
    "input_tokens": 1200,
    "cached_input_tokens": 200,
    "output_tokens": 300,
    "total_tokens": 1500,
    "cost_usd": 0.01,
    "turns": 2,
    "wall_seconds": 0.05,
}


class DocumentSource(str):
    """One Protocol-8 fixture unit, optionally accompanied by explicitly authored precise reading."""

    metadata: dict
    implementation: "DocumentSource | None"

    def __new__(cls, reading, metadata, implementation=None):
        if metadata["document"]["role"] == "module" and "## Terminology" not in reading:
            terms = "## Terminology\n\nNo specialized terminology.\n\n"
            if "## Usage" in reading:
                reading = reading.replace("## Usage", terms + "## Usage", 1)
            else:
                title, _, rest = reading.partition("\n")
                reading = title + "\n\n" + terms + "## Details\n\n" + rest
        value = super().__new__(cls, reading)
        value.metadata = metadata
        value.implementation = implementation
        return value


def write_document(root, path, source):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(str(source))
    if isinstance(source, DocumentSource):
        (root / (path + ".json")).write_text(
            json.dumps(source.metadata, indent=2) + "\n"
        )
        if source.implementation is not None:
            precise = str(Path(path).with_name("obligations.md"))
            write_document(root, precise, source.implementation)
            # This fixture author explicitly registers the two-role collection it just wrote.
            registry_path = root / ".concorde/specs.json"
            if registry_path.is_file():
                registry = json.loads(registry_path.read_text())
                for target in registry["targets"]:
                    if (
                        path in target["documents"]
                        and precise not in target["documents"]
                    ):
                        target["documents"].append(precise)
                registry_path.write_text(json.dumps(registry))


def source_pairs(paths):
    return sorted(member for path in paths for member in (path, path + ".json"))


def add_binding(root, path, binding):
    metadata_path = root / (path + ".json")
    metadata = json.loads(metadata_path.read_text())
    anchor = (
        "participation."
        + metadata["document"]["id"]
        + "."
        + str(len(metadata["bindings"]))
    )
    metadata["bindings"].append(
        {key: binding[key] for key in ("id", "version", "role", "peer")}
        | {"meaning": "#" + anchor}
    )
    body = (root / path).read_text()
    body += (
        f'\n### Participation\n\n<a id="{anchor}"></a>\n\n'
        + binding["selection_condition"]
        + "\n\n"
        + "\n\n".join(binding["relied_upon_guarantees"])
        + "\n\n"
        + "\n\n".join(binding["obligations"])
        + "\n"
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    (root / path).write_text(body)


def update_entities(root, path, update):
    metadata_path = root / (path + ".json")
    metadata = json.loads(metadata_path.read_text())
    metadata["entities"] = update(metadata["entities"])
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")


def update_document_declaration(root, path, **updates):
    document = root / (path + ".json")
    value = json.loads(document.read_text())
    value["document"].update(updates)
    document.write_text(json.dumps(value, indent=2) + "\n")


def block(name, value):
    return "```" + name + "\n" + json.dumps(value, indent=2) + "\n```\n"


def module_document(
    document_id,
    target_id,
    title,
    purpose,
    scenarios,
    entities,
    architecture,
    diagram,
    dependencies=(),
    trailer="",
    requirements="No Module-level requirement is stated here.",
):
    metadata = {
        "schema_version": 2,
        "document": {"id": document_id, "owner": target_id, "role": "module"},
        "entities": [],
        "dependencies": [],
        "bindings": [],
    }
    entity_prose = []
    for entity in entities[1]:
        metadata["entities"].append(
            {
                **{k: v for k, v in entity.items() if k != "responsibility"},
                "meaning": "#" + entity["id"],
            }
        )
        entity_prose.append(
            f'<a id="{entity["id"]}"></a>\n\n{entity["responsibility"]}'
        )
    text = (
        f"# {title}\n\n## Purpose\n\n{purpose}\n\n## Usage\n\n"
        "Use the declared boundary for the cases below; rejected input has no implicit retry.\n\n"
        f"## Design\n\n{architecture}\n\n"
        + "\n\n".join(entity_prose)
        + "\n\n## Relationships\n\nThis view shows the declared local collaboration.\n\n"
        f"```mermaid\n{diagram}\n```\n"
    )
    if dependencies:
        text += "\n## Collaborators\n"
        for index, dependency in enumerate(dependencies):
            anchor = f"agreement.{document_id}.{index}"
            metadata["dependencies"].append(
                {"target_id": dependency["target_id"], "meaning": "#" + anchor}
            )
            text += (
                f'\n<a id="{anchor}"></a>\n\n'
                + dependency["responsibility"]
                + "\n\n"
                + dependency["selection_condition"]
                + "\n\n"
                + "\n".join(
                    "- " + promise for promise in dependency["relied_upon_promises"]
                )
                + "\n"
            )
    precise = DocumentSource(
        f"# {title} obligations\n\n## Requirements\n\n{requirements}\n\n## Scenarios\n\n{scenarios}\n"
        + trailer,
        {
            "schema_version": 2,
            "document": {
                "id": document_id + ".obligations",
                "owner": target_id,
                "role": "implementation",
            },
            "entities": [],
            "dependencies": [],
            "bindings": [],
        },
    )
    return DocumentSource(text, metadata, precise)


def promise(peer):
    return {
        "target_id": peer,
        "responsibility": "Provide the locally described " + peer + " responsibility.",
        "selection_condition": "Select for work about " + peer + ".",
        "relied_upon_promises": [
            "Transfer accepts positive affordable amounts; ledger reads return "
            "an integer or KeyError; audit records successful balance changes."
        ],
    }


BANK = module_document(
    "document.bank",
    "scope.bank",
    "Banking",
    "Banking coordinates money movement between customer accounts. It performs no calculation of\n"
    "its own: transfer admission and execution belong to the transfer Module, stored balances to\n"
    "the ledger Module, and audit outcomes to the audit Module.",
    "### scenario.bank.settlement — A completed transfer settles both accounts\n\n"
    "- GIVEN a sender account whose balance covers the requested amount\n"
    "- WHEN Banking accepts one transfer request\n"
    "- THEN the sender is debited and the receiver is credited\n"
    "- AND the audit Module receives the accepted balance change\n"
    "- AND a repeated request is treated as a new decision\n",
    (
        "Banking owns the request concept; every other entity stands for a Module it composes with.",
        [
            {
                "id": "entity.bank.request",
                "title": "Transfer request",
                "kind": "concept",
                "responsibility": "Carries the sender, the receiver and the requested amount.",
            },
            {
                "id": "entity.bank.transfer",
                "title": "Transfer service",
                "kind": "module",
                "responsibility": "Admits and executes one transfer.",
                "target_id": "service.transfer",
            },
            {
                "id": "entity.bank.ledger",
                "title": "Ledger",
                "kind": "module",
                "responsibility": "Stores the account balances Banking settles against.",
                "target_id": "module.ledger",
            },
            {
                "id": "entity.bank.audit",
                "title": "Audit",
                "kind": "module",
                "responsibility": "Describes the audit outcome of an accepted change.",
                "target_id": "scope.audit",
            },
        ],
    ),
    "A transfer request is admitted by the transfer Module, which reads balances from the ledger\n"
    "Module. The audit Module observes the accepted change without owning either provider.",
    "flowchart TB\n"
    "    accTitle: Banking coordination\n"
    "    accDescr: A transfer request reaches the transfer service, which reads balances from the ledger and reports accepted changes to audit.\n"
    '    request["Transfer request"]\n    transfer["Transfer service"]\n'
    '    ledger["Ledger"]\n    audit["Audit"]\n'
    "    request -->|admitted by| transfer\n"
    "    transfer -->|reads balances from| ledger\n"
    "    transfer -->|reports accepted changes to| audit",
    [promise(peer) for peer in ("service.transfer", "module.ledger", "scope.audit")],
    requirements="### req.bank.retry — Repeated requests are new decisions\n\n"
    "Banking SHALL treat a repeated request as a new decision.\n",
)

AUDIT = module_document(
    "document.audit",
    "scope.audit",
    "Audit",
    "Audit describes the outcome an accepted balance change must produce. It owns no transfer\n"
    "calculation and no stored balance of its own.",
    "### scenario.audit.record — An accepted transfer becomes one audit record\n\n"
    "- GIVEN a transfer the transfer Module reports as successful\n"
    "- WHEN Audit receives that accepted balance change\n"
    "- THEN one audit record describes the sender, the receiver and the amount\n",
    (
        "Audit owns its record concept and observes the transfer Module.",
        [
            {
                "id": "entity.audit.transfer",
                "title": "Transfer service",
                "kind": "module",
                "responsibility": "Reports successful balance changes.",
                "target_id": "service.transfer",
            },
            {
                "id": "entity.audit.record",
                "title": "Audit record",
                "kind": "concept",
                "responsibility": "Describes one accepted balance change.",
            },
        ],
    ),
    "The transfer Module produces the accepted change that Audit turns into a record.",
    "flowchart TB\n"
    "    accTitle: Audit outcomes\n"
    "    accDescr: The transfer service produces the accepted balance change that becomes one audit record.\n"
    '    transfer["Transfer service"]\n    record["Audit record"]\n'
    "    transfer -->|produces| record",
    [promise("service.transfer")],
)

TRANSFER = module_document(
    "document.transfer.feature",
    "service.transfer",
    "Transfer money",
    "The transfer Module admits one money movement and computes its result. Calls are pure: the\n"
    "Module reads stored balances through the ledger Module and stores nothing itself.",
    "### scenario.transfer.debit — A valid amount debits the sender\n\n"
    "- GIVEN a sender balance of 100\n"
    "- WHEN transfer(100, 20) is called\n"
    "- THEN it returns 80\n"
    "- AND no stored balance changes\n\n"
    "### scenario.transfer.reject — An unaffordable or non-positive amount is rejected\n\n"
    "- GIVEN a sender balance of 10\n"
    "- WHEN transfer(10, 20) is called\n"
    "- THEN it raises ValueError\n"
    "- AND no balance changes\n",
    (
        "The calculation and its executable check are the Module's own code; the ledger Module\n"
        "supplies stored balances.",
        [
            {
                "id": "entity.transfer.calculation",
                "title": "Transfer calculation",
                "kind": "function",
                "responsibility": "Computes the remaining balance, or rejects the requested amount.",
                "files": ["app/transfer.py"],
            },
            {
                "id": "entity.transfer.check",
                "title": "Transfer check",
                "kind": "executable check",
                "responsibility": "Exercises one accepted amount and every rejected amount.",
                "files": ["checks/transfer_check.py"],
            },
            {
                "id": "entity.transfer.ledger",
                "title": "Ledger",
                "kind": "module",
                "responsibility": "Supplies stored balances through read(account_id).",
                "target_id": "module.ledger",
            },
        ],
    ),
    "The check exercises the calculation, which reads stored balances from the ledger Module.\n"
    "Ledger API tasks are separately bound to that Module.",
    "flowchart TB\n"
    "    accTitle: Transfer money\n"
    "    accDescr: The transfer check exercises the transfer calculation, which reads stored balances from the ledger.\n"
    '    check["Transfer check"]\n    calculation["Transfer calculation"]\n    ledger["Ledger"]\n'
    "    check -->|exercises| calculation\n"
    "    calculation -->|reads balances from| ledger",
    [promise("module.ledger")],
    requirements="### req.transfer.pure — Transfers store nothing\n\n"
    "transfer SHALL NOT alter any stored balance.\n",
)

LEDGER = module_document(
    "document.ledger.api",
    "module.ledger",
    "Ledger API",
    "The ledger Module stores account balances and answers one read per account identity.",
    "### scenario.ledger.read — A stored account returns its balance\n\n"
    "- GIVEN an account with a stored balance\n"
    "- WHEN read(account_id) is called\n"
    "- THEN it returns that integer balance\n\n"
    "### scenario.ledger.unknown — An unknown identity is an explicit failure\n\n"
    "- GIVEN no stored balance for the requested identity\n"
    "- WHEN read(account_id) is called\n"
    "- THEN it raises KeyError\n",
    (
        "Accounts map to integer balances held by the balance store.",
        [
            {
                "id": "entity.ledger.account",
                "title": "Account",
                "kind": "concept",
                "responsibility": "Identifies exactly one stored balance.",
            },
            {
                "id": "entity.ledger.store",
                "title": "Balance store",
                "kind": "data store",
                "responsibility": "Maps account identities to integer balances and rejects unknown ones.",
                "files": ["app/ledger.py"],
            },
        ],
    ),
    "An account identity indexes the balance store. Unknown identity is an explicit lookup failure.",
    "flowchart TB\n"
    "    accTitle: Ledger API\n"
    "    accDescr: An account identity indexes the balance store, which answers with an integer balance or an explicit failure.\n"
    '    account["Account"]\n    store["Balance store"]\n'
    "    account -->|indexes| store",
)

PROMISES = DocumentSource(
    "# Local promises\n\nBalance and amount are integers. No network, persistence or implicit\n"
    "retry is performed by transfer. This complete collection defines all facts required to\n"
    "implement and test transfer.\n",
    {
        "schema_version": 2,
        "document": {
            "id": "document.transfer.promises",
            "owner": "service.transfer",
            "role": "module",
        },
        "entities": [],
        "dependencies": [],
        "bindings": [],
    },
)


def project(root):
    install_project_defaults(
        root, PACKAGE
    )  # what the installer places before initialization
    apply_project_proposal(
        root,
        PACKAGE,
        project_proposal(root, PACKAGE, "Bank", CONFIGURATION, "scope.bank"),
    )
    targets = [
        empty_target("scope.bank", "module", "Banking", ["specs/bank/module.md"]),
        empty_target("scope.audit", "module", "Audit", ["specs/audit/module.md"]),
        empty_target(
            "service.transfer",
            "module",
            "Transfers",
            ["specs/transfer/module.md", "specs/transfer/promises.md"],
        ),
        empty_target("module.ledger", "module", "Ledger", ["specs/ledger/module.md"]),
    ]
    targets[0]["uses"] = ["service.transfer", "module.ledger", "scope.audit"]
    targets[1]["uses"] = ["service.transfer"]
    targets[2].update(
        uses=["module.ledger"],
        files=["app/transfer.py", "checks/transfer_check.py"],
        checks=["check.transfer"],
    )
    targets[3].update(files=["app/ledger.py"])
    registry = {
        "schema_version": 5,
        "project_id": "project.bank",
        "entry_target": "scope.bank",
        "targets": targets,
        "checks": [
            {
                "id": "check.transfer",
                "target_id": "service.transfer",
                "argv": ["{python}", "checks/transfer_check.py"],
                "timeout_seconds": 10,
            }
        ],
    }
    for target in targets:
        target["documents"].append(
            str(Path(target["documents"][0]).with_name("obligations.md"))
        )
    (root / ".concorde/specs.json").write_text(json.dumps(registry))
    files = {
        "specs/bank/module.md": BANK,
        "specs/audit/module.md": AUDIT,
        "specs/transfer/module.md": TRANSFER,
        "specs/transfer/promises.md": PROMISES,
        "specs/ledger/module.md": LEDGER,
        "app/transfer.py": "# TRANSFER_IMPLEMENTATION_CODE\ndef transfer(balance, amount):\n    return balance\n",
        "app/ledger.py": "# LEDGER_IMPLEMENTATION_CODE\ndef read(account_id):\n    raise KeyError(account_id)\n",
        "checks/transfer_check.py": 'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom app.transfer import transfer\nassert transfer(100,20)==80\nfor balance,amount in [(10,20),(10,0),(10,-1)]:\n    try: transfer(balance,amount)\n    except ValueError: pass\n    else: raise AssertionError("invalid transfer accepted")\n',
        "secret.py": "PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT = True\n",
    }
    for path, content in files.items():
        write_document(root, path, content)
    return registry


class ModelProcessDouble:
    """Stands in for the Pi worker process only: the worker executor, its preflight, the contract
    checks and every host admission stay real. ``run`` has the Pi worker runtime's signature."""

    executor: Callable[..., WorkerOutcome]

    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback
        self.reporter = None
        self.executor = WorkerExecutor(PACKAGE, runtime=self.run)

    def fixture_reports(self, data):
        """Author fixture observations through the real report service; not a runtime adapter.

        Historical test helpers describe findings as prose. Convert that authoring notation into
        the new wire references here so every host/executor still sees the actual Issue contract.
        """
        reporter = self.reporter
        if reporter is None:
            return
        from concorde.spec.repository import SpecError

        def observed(problem, basis, impact, key, owner=None, evidence=(), kind="gap"):
            return reporter(
                {
                    "report_key": key,
                    "type": kind,
                    "subtype": "missing-contract" if kind == "gap" else None,
                    "title": problem,
                    "description": problem,
                    "basis": basis,
                    "impact": impact,
                    "owner_target_id": owner or reporter.source["target_id"],
                    "evidence": list(evidence),
                }
            )["receipt"]

        blockers = data.get("blockers", [])
        if "review_mode" in data:
            findings = data.get("issues", [])
            converted = []
            for item in findings:
                if "issue_id" in item:
                    converted.append(item)
                    continue
                proof = [
                    {"path": item["location"]["path"], "description": item["contract"]}
                ]
                if item["document"] != item["location"]["path"]:
                    proof.append(
                        {"path": item["document"], "description": item["contract"]}
                    )
                ref = observed(
                    item["problem"],
                    item["contract"],
                    item["affected_task"],
                    item["id"],
                    item["target_id"],
                    proof,
                    kind="gap" if data["review_mode"] == "spec" else "bug",
                )
                converted.append(
                    {
                        **ref,
                        "severity": item["severity"],
                        "affected_task": item["affected_task"],
                    }
                )
            for index, gap in enumerate(blockers):
                if any(
                    item.get("affected_task") == gap.get("blocked_step")
                    for item in converted
                ):
                    continue
                if "issue_id" in gap:
                    ref = {key: gap[key] for key in ("issue_id", "report_id", "path")}
                else:
                    ref = observed(
                        gap["question"],
                        gap["needed_contract"],
                        gap["blocked_step"],
                        "gap-" + str(index),
                    )
                converted.append(
                    {
                        **ref,
                        "severity": "blocking",
                        "affected_task": gap["blocked_step"],
                    }
                )
            data.pop("blockers", None)
            if "issues" in data:
                data["issues"] = converted
        else:
            for index, gap in enumerate(blockers):
                if "issue_id" in gap:
                    continue
                if (
                    gap.get("context_id", reporter.source["context_id"])
                    != reporter.source["context_id"]
                ):
                    raise SpecError(
                        "fixture blocker provenance differs from the admitted context",
                        "incompatible_handoff",
                    )
                ref = observed(
                    gap["question"],
                    gap["needed_contract"],
                    gap["blocked_step"],
                    "blocker-" + str(index),
                    owner=gap.get("target_id"),
                )
                blockers[index] = {**ref, "blocked_step": gap["blocked_step"]}

    def result(self, data):
        self.fixture_reports(data)
        # DocumentSource explicitly carries a paired fixture proposal; serialize both members
        # into the worker's ordinary path/content list before the JSON transport round trip.
        documents = data.get("documents", [])
        for item in list(documents):
            source = item["content"]
            if isinstance(source, DocumentSource):
                item["content"] = str(source)
                path = item["path"] + ".json"
                partner = next(
                    (entry for entry in documents if entry["path"] == path), None
                )
                if partner is None:
                    partner = {"path": path, "content": ""}
                    documents.insert(documents.index(item) + 1, partner)
                partner["content"] = json.dumps(source.metadata, indent=2) + "\n"
                if source.implementation is not None:
                    precise_path = str(Path(item["path"]).with_name("obligations.md"))
                    for p, content in (
                        (precise_path, str(source.implementation)),
                        (
                            precise_path + ".json",
                            json.dumps(source.implementation.metadata, indent=2) + "\n",
                        ),
                    ):
                        existing = next(
                            (entry for entry in documents if entry["path"] == p), None
                        )
                        if existing is None:
                            documents.append({"path": p, "content": content})
                        else:
                            existing["content"] = content
        return WorkerResult(
            value=json.loads(json.dumps(data)),
            run=PiRun(exit_code=0),
            usage=dict(USAGE),
        )

    def run(self, launch, *, checks=None, report_issue=None):
        self.reporter = report_issue
        agent = worker_profile(launch.worker)
        stage = agent.contract.phase
        operation = external_worker_name(agent.name)
        cwd = launch.workspace
        value = json.loads(launch.message)
        snapshot = (
            value["data"]["snapshot"]["data"]
            if value["type_id"]
            in {
                "concorde-agent-stage-context",
                "concorde-review-stage-context",
            }
            else value["data"]
        )
        # The index lists every granted Spec document and Protocol file; a real worker opens them from
        # its workspace, so the double proves each one is granted and present there with the frozen bytes.
        index = {
            item["path"]: item["digest"]
            for item in (
                *snapshot["protocol"],
                *(
                    snapshot["spec_resolution"]["sources"]
                    if "spec_resolution" in snapshot
                    else snapshot["documents"]
                ),
            )
        }
        for path, expected in index.items():
            granted = Path(cwd) / path
            if (
                path not in launch.read_paths
                or not granted.is_file()
                or "sha256:" + hashlib.sha256(granted.read_bytes()).hexdigest()
                != expected
            ):
                raise AssertionError(
                    f"granted context file missing, ungranted or changed in the workspace: {path}"
                )
        self.calls.append(
            {
                "stage": stage,
                "operation": operation,
                "agent": agent.name,
                "snapshot": snapshot,
                "cwd": Path(cwd),
                "prompt": launch.system_prompt + "\n" + launch.message,
                "launch": launch,
                "timeout": launch.timeout_seconds,
                "granted": sorted(index),
                "checks": checks,
                "report_issue": report_issue,
            }
        )
        if value["type_id"] == "concorde-review-stage-context":
            review = value["data"]["review"]["data"]
            self.calls[-1]["review"] = review
            data = {
                "context_id": snapshot["context_id"],
                "input_digest": review["input_digest"],
                "review_mode": review["review_mode"],
                "status": "no_findings",
                "representative_tasks": [snapshot["task"]],
                "issues": [],
                "answer": "Explicit process double completed; model effectiveness is not measured.",
            }
            if self.callback:
                self.callback(stage, snapshot, data, Path(cwd))
            return self.result(data)
        data = {
            "context_id": snapshot["context_id"],
            "outcome": "completed",
            "answer": "Bounded role completed.",
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
        }
        if stage == "issue-solve":
            selection = snapshot["stage_inputs"][0]["data"]
            action = (
                "resolved"
                if selection["verification"]
                else "verify"
                if "Development and" in selection["feedback"]
                else "develop"
            )
            data["issue_decision"] = {
                "action": action,
                "intent": "Fulfil the specified pure transfer behavior.",
                "rationale": "The current contract defines the expected transfer behavior.",
                "duplicate_of": None,
            }
        if stage == "context-solve":
            data["outcome"] = "sufficient"
        if stage == "plan":
            data["plan"] = (
                "Implement the pure transfer contract, then check valid and rejected amounts."
            )
        if stage == "tasks":
            task_target = snapshot["target_id"]
            if snapshot["target_id"] in {"scope.bank", "scope.audit"}:
                declarations = [
                    json.loads((Path(cwd) / item["path"]).read_text())
                    for item in snapshot["spec_resolution"]["sources"]
                    if item["role"] == "metadata"
                ]
                dependencies = [
                    d for value in declarations for d in value["dependencies"]
                ]
                if not dependencies:
                    raise AssertionError(
                        "Module task fixture requires local participant declarations"
                    )
                task_target = dependencies[0]["target_id"]
            data["tasks"] = [
                {
                    "id": "task.transfer",
                    "target_id": task_target,
                    "description": "Implement the transfer promise.",
                    "acceptance": "Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.",
                    "complete": False,
                }
            ]
        if (
            stage == "implementation"
            and snapshot["stage_inputs"][0]["type_id"] == "concorde-implementation-task"
        ):
            if snapshot["target_id"] == "module.ledger":
                (Path(cwd) / "app/ledger.py").write_text(
                    '# LEDGER_IMPLEMENTATION_CODE\ndef read(account_id):\n    balances = {"known": 100}\n    return balances[account_id]\n'
                )
            else:
                (Path(cwd) / "app/transfer.py").write_text(
                    '# TRANSFER_IMPLEMENTATION_CODE\ndef transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n'
                )
            task_input = snapshot["stage_inputs"][0]["data"]
            data["tasks"] = [{**task, "complete": True} for task in task_input["tasks"]]
        if self.callback:
            self.callback(stage, snapshot, data, Path(cwd))
        return self.result(data)
