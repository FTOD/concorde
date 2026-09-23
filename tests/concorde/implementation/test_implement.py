"""``concorde-implement`` driven through the native driver against a real candidate worktree.

Every call is prepared, submitted, staged and accepted by the native driver's own actions, as the
Pi session's call extension and gate would run them; only the native records a pi-subagents run
leaves behind are written synthetically. No Pi, pi-subagents or model runs.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import bind_owner, ensure_change, read_change
from concorde.harness.configuration import load_configuration
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.native_driver import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.harness.revisions import implementation_digest, target_revision
from concorde.operations.dispatch import services
from concorde.planning.plan import persist_plan_result
from concorde.planning.records import save_target_state, target_state, targets
from concorde.planning.scope import component_intent
from concorde.planning.tasks import persist_tasks
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import canonical, typed
from concorde.spec.verification import verifies
from tests.concorde.support.shared_file_project import SharedFileFixture
from tests.concorde.support.spec_project import PACKAGE, project

OWNER = "service.transfer"
COMPONENT = "module.ledger"
TASK = {"target_id": OWNER, "task": "Implement the transfer contract"}
SHARED_TASK = {"target_id": "module.a", "task": "Adapt the shared value"}
LAUNCH = "sha256:" + "1" * 64
CONTROL = (
    "schema_version",
    "ticket",
    "invocation_id",
    "proposal_digest",
    "state",
    "accepted",
)


def local_task(identity="task.implement", target=OWNER, description=None):
    return {
        "id": identity,
        "target_id": target,
        "description": description or "Implement " + identity,
        "acceptance": "Valid inputs subtract and invalid inputs raise ValueError",
        "complete": False,
    }


def codes(value):
    return {entry["code"] for entry in value["result"]["errors"]}


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


class Candidate:
    """A managed candidate with an accepted plan and task list; ``tasks`` sets the list."""

    tasks = (local_task(),)

    def write_project(self, root: Path) -> None:
        project(root)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        base = Path(self.scratch.name)
        self.calls = base / "tmp"
        self.calls.mkdir()
        tempdir = patch.object(tempfile, "tempdir", str(self.calls))
        tempdir.start()
        self.addCleanup(tempdir.stop)
        self.native = base / "native"
        self.native.mkdir()
        runtime = patch(
            "concorde.harness.native_driver.admit_native_runtime",
            return_value=NativeRuntimeBinding(
                FORMAT, str(self.native), "sha256:" + "0" * 64
            ),
        )
        runtime.start()
        self.addCleanup(runtime.stop)
        self.primary = base / "primary"
        self.primary.mkdir()
        self.write_project(self.primary)
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Fixture")
        git(self.primary, "config", "user.email", "fixture@example.invalid")
        git(self.primary, "add", "-A")
        git(self.primary, "commit", "-qm", "Fixture")
        self.root = base / "candidate"
        git(self.primary, "worktree", "add", "-q", "-b", "programmer", str(self.root))
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.root)
        ensure_change(self.root, task=self.task)
        bind_owner(self.root, self.task)
        self.plan(self.task, list(self.tasks))

    task = TASK

    # -- the accepted plan and tasks, as Planning records them -----------------------------

    def invocation(self, task):
        return Invocation(
            "concorde-implement",
            load_configuration(self.root),
            task,
            OperationHost(self.root, PACKAGE),
        )

    def plan(self, task, tasks):
        run = self.invocation(task)
        persist_plan_result(
            run, {"plan": "Implement " + task["target_id"], "answer": "Seed"}
        )
        state = target_state(self.root, task["target_id"], None)
        persist_tasks(run, {"tasks": tasks, "answer": "Seed"}, state, None, None)

    def state(self, target=None):
        return targets(read_change(self.root, required=True))[
            target or self.task["target_id"]
        ]

    def update(self, change, target=None):
        state = target_state(self.root, target or self.task["target_id"], None)
        change(state)
        save_target_state(self.root, state)

    # -- native actions ------------------------------------------------------------------

    def prepare(self, task=None):
        task = task or self.task
        envelope = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-implement",
            "mode": "execute",
            "configuration": None,
            "input": typed("concorde-implement-request", task),
        }
        return execute(
            PACKAGE,
            "prepare",
            {
                "invocation": envelope,
                "native_root": str(self.native),
                "session_id": "unit",
            },
            services=services(),
        )

    def command(self, prepared, action, payload=None):
        return execute(
            PACKAGE,
            action,
            {} if payload is None else payload,
            prepared["descriptor"],
            prepared["digest"],
            services=services(),
        )

    def descriptor(self, prepared):
        return json.loads(Path(prepared["descriptor"]).read_text())

    def index(self, prepared):
        return json.loads(
            (Path(prepared["descriptor"]).parent / "context/context.json").read_text()
        )

    def admitted_tasks(self, prepared):
        (value,) = [
            item
            for item in self.descriptor(prepared)["stage_inputs"]
            if item["type_id"] == "concorde-implementation-task"
        ]
        return value["data"]["tasks"]

    def proposal(self, prepared, tasks=None, outcome="completed"):
        if tasks is None:
            tasks = [
                {**task, "complete": True} for task in self.admitted_tasks(prepared)
            ]
        return {
            "invocation_id": prepared["ticket"],
            "result": typed(
                "concorde-agent-stage-result",
                {
                    "context_id": self.descriptor(prepared)["snapshot"]["context_id"],
                    "outcome": outcome,
                    "answer": "Scripted programmer answer",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": tasks,
                },
            ),
        }

    def submit_and_stage(self, prepared, **proposal):
        value = self.proposal(prepared, **proposal)
        submitted = self.command(prepared, "submit", value)
        self.assertEqual("proposed", submitted.get("state"), submitted)
        staged = self.command(prepared, "stage")
        self.assertEqual("staged", staged.get("state"), staged)
        return value, {key: staged[key] for key in CONTROL}

    def evidence(self, prepared, proposal, control, **row):
        """The correlated native result of a finished run, with its records on disk."""
        records = Path(self.scratch.name) / "records" / prepared["ticket"]
        records.mkdir(parents=True)
        (records / "output.json").write_text(canonical(proposal))
        gate = prepared["call"]["gate"]["command"]
        (records / "metadata.json").write_text(
            canonical(
                {
                    "runId": "run-1",
                    "agent": prepared["call"]["agent"],
                    "launchContractDigest": LAUNCH,
                    "exitCode": 0,
                    "acceptance": {
                        "status": "verified",
                        "verifyRuns": [
                            {
                                "command": gate,
                                "status": "passed",
                                "exitCode": 0,
                                "stdout": canonical(control),
                            }
                        ],
                    },
                }
            )
        )
        return {
            "details": {
                "mode": "single",
                "runId": "run-1",
                "results": [
                    {
                        "agent": prepared["call"]["agent"],
                        "exitCode": 0,
                        "launchContractDigest": LAUNCH,
                        "structuredOutputPath": str(records / "output.json"),
                        "artifactPaths": {
                            "metadataPath": str(records / "metadata.json")
                        },
                        **row,
                    }
                ],
            },
            "isError": False,
            "tool_call_id": "tool-" + prepared["ticket"],
            "session_id": "unit",
            "launch_contract_digest": LAUNCH,
            "gate_command": gate,
        }

    def edit(self, relative="app/transfer.py", text="# programmer edit\n"):
        """What the programmer's edit tool does: change a file of the real candidate."""
        path = self.root / relative
        path.write_text(path.read_text() + text)
        return path.read_text()

    def run_programmer(self, prepared, **row):
        """Edit, submit, stage and accept one prepared programmer call."""
        self.edit()
        proposal, control = self.submit_and_stage(prepared)
        return self.command(
            prepared, "accept", self.evidence(prepared, proposal, control, **row)
        )

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def assert_not_ready(self):
        change = read_change(self.root, required=True)
        self.assertNotEqual("ready", change.get("outcome"))
        self.assertNotEqual("ready", change.get("phase"))

    def assert_no_completion(self, target=None):
        state = self.state(target)
        self.assertFalse(any(task["complete"] for task in state["tasks"]), state)
        self.assertIsNone(state.get("implementation_digest"))
        self.assertNotEqual("completed", state.get("status"))

    def assert_no_call(self, value, before=frozenset()):
        self.assertNotIn("call", value)
        self.assertNotIn("descriptor", value)
        self.assertEqual(set(before), set(self.calls.iterdir()))

    def complete_component(self, tasks, target=COMPONENT, file="app/ledger.py"):
        """The user session's component work: plan, tasks and implementation of ``target``."""
        component = {"target_id": target, "task": component_intent(tasks)}
        bind_owner(self.root, component, component=True)
        self.plan(component, [local_task("task.component", target)])
        prepared = self.prepare(component)
        self.assertEqual("prepared", prepared.get("state"), prepared)
        self.edit(file, "# component edit\n")
        proposal, control = self.submit_and_stage(prepared)
        value = self.command(
            prepared, "accept", self.evidence(prepared, proposal, control)
        )
        self.assertTrue(value.get("accepted"), value)
        return component


class LocalWorkTests(Candidate, unittest.TestCase):
    @verifies("scenario.implementation.admitted-work")
    def test_every_local_task_fulfilled_is_accepted_as_completion(self):
        spec = git(self.root, "status", "--porcelain", "specs")
        prepared = self.prepare()
        self.assertEqual("prepared", prepared["state"], prepared)
        self.assertEqual([task for task in self.tasks], self.admitted_tasks(prepared))
        edited = self.edit()
        proposal, control = self.submit_and_stage(prepared)
        value = self.command(
            prepared, "accept", self.evidence(prepared, proposal, control)
        )
        self.assertTrue(value["accepted"], value)
        self.assertEqual("succeeded", value["result"]["status"], value)
        state = self.state()
        self.assertEqual(
            [{**task, "complete": True} for task in self.tasks], state["tasks"]
        )
        self.assertEqual(
            implementation_digest(self.repository(), self.repository().module(OWNER)),
            state["implementation_digest"],
        )
        self.assertEqual(
            ("implementation", "completed"), (state["phase"], state["status"])
        )
        self.assertEqual(edited, (self.root / "app/transfer.py").read_text())
        # No Spec changes and no readiness: checks and reviews stay separate.
        self.assertEqual(spec, git(self.root, "status", "--porcelain", "specs"))
        self.assertEqual([], state["checks"])
        self.assert_not_ready()

    @verifies("scenario.implementation.changed-inputs")
    def test_changed_plan_tasks_feedback_or_spec_accept_no_completion(self):
        changes = {
            "plan": lambda: self.update(lambda s: s.update(plan="Changed plan")),
            "tasks": lambda: self.update(
                lambda s: s["tasks"][0].update(acceptance="Changed acceptance")
            ),
            "review feedback": lambda: self.update(
                lambda s: s.update(
                    repair_review={
                        "id": "review",
                        "path": ".concorde/work/foreign.json",
                        "digest": "sha256:" + "0" * 64,
                    }
                )
            ),
            "spec": lambda: (self.root / "specs/transfer/module.md").write_text(
                (self.root / "specs/transfer/module.md").read_text()
                + "\nChanged contract\n"
            ),
        }
        for label, change in changes.items():
            with self.subTest(label):
                prepared = self.prepare()
                self.assertEqual("prepared", prepared["state"], prepared)
                edited = self.edit(text=f"# edit before {label} changed\n")
                proposal, control = self.submit_and_stage(prepared)
                change()
                value = self.command(
                    prepared, "accept", self.evidence(prepared, proposal, control)
                )
                self.assertEqual("rejected", value["state"], value)
                self.assertTrue(
                    codes(value) & {"stale_context", "stale_reference"}, value
                )
                self.assertFalse(value["accepted"])
                self.assertFalse(
                    (Path(prepared["descriptor"]).parent / "terminal.json").exists()
                )
                self.assert_no_completion()
                self.assertEqual(edited, (self.root / "app/transfer.py").read_text())
                # Restore the accepted inputs for the next case.
                git(self.root, "checkout", "--", "specs")
                self.update(
                    lambda s: (
                        s.update(plan="Implement " + OWNER, tasks=list(self.tasks)),
                        s.pop("repair_review", None),
                    )
                )

    @verifies("scenario.implementation.incomplete-output")
    def test_an_answer_that_misses_changes_or_leaves_a_task_open_is_incomplete(self):
        self.update(
            lambda s: s.update(tasks=[local_task("task.one"), local_task("task.two")])
        )
        for label, tasks in {
            "omitted": lambda admitted: [{**admitted[0], "complete": True}],
            "changed": lambda admitted: [
                {**task, "complete": True, "acceptance": "Weaker acceptance"}
                for task in admitted
            ],
            "incomplete": lambda admitted: [
                {**admitted[0], "complete": True},
                {**admitted[1], "complete": False},
            ],
        }.items():
            with self.subTest(label):
                prepared = self.prepare()
                self.assertEqual("prepared", prepared["state"], prepared)
                edited = self.edit(text=f"# {label} edit\n")
                answer = self.proposal(
                    prepared, tasks=tasks(self.admitted_tasks(prepared))
                )
                submitted = self.command(prepared, "submit", answer)
                self.assertEqual("rejected", submitted["state"], submitted)
                self.assertIn("incomplete_tasks", codes(submitted))
                for action in ("stage", "accept"):
                    self.assertEqual(
                        "rejected", self.command(prepared, action, {})["state"]
                    )
                self.assert_no_completion()
                self.assertEqual(edited, (self.root / "app/transfer.py").read_text())
                self.assert_not_ready()

    @verifies("scenario.implementation.incomplete-output")
    def test_a_missing_listed_file_is_incomplete(self):
        prepared = self.prepare()
        (self.root / "checks/transfer_check.py").unlink()
        answer = self.proposal(prepared)
        submitted = self.command(prepared, "submit", answer)
        self.assertEqual("rejected", submitted["state"], submitted)
        self.assertIn("incomplete_tasks", codes(submitted))
        self.assert_no_completion()

    @verifies("scenario.implementation.failed-execution")
    def test_a_failed_or_cancelled_run_keeps_edits_and_records_nothing(self):
        for label, row in {
            "failed": {"exitCode": 1},
            "cancelled": {"interrupted": True},
        }.items():
            with self.subTest(label):
                prepared = self.prepare()
                self.assertEqual("prepared", prepared["state"], prepared)
                tools = self.descriptor(prepared)["launch"]
                value = self.run_programmer(prepared, **row)
                self.assertEqual("rejected", value["state"], value)
                self.assertEqual(
                    {
                        "failed": {"execution_failed"},
                        "cancelled": {"execution_cancelled"},
                    }[label],
                    codes(value),
                )
                self.assertFalse(value["accepted"])
                self.assert_no_completion()
                self.assertIn(
                    "# programmer edit", (self.root / "app/transfer.py").read_text()
                )
                # The call extension invalidates the failed call; nothing accepts it later.
                self.command(prepared, "invalidate", {"reason": label})
                self.assertEqual("rejected", self.command(prepared, "stage")["state"])
                # The candidate and its recorded progress stay available.
                self.assertEqual(
                    "implementation", read_change(self.root, required=True)["phase"]
                )
                self.assertEqual("Implement " + OWNER, self.state()["plan"])
                self.assertEqual(list(self.tasks), self.state()["tasks"])
                # A later attempt is a fresh preparation of the current inputs, no wider.
                again = self.prepare()
                self.assertEqual("prepared", again["state"], again)
                self.assertNotEqual(prepared["ticket"], again["ticket"])
                self.assertNotEqual(prepared["descriptor"], again["descriptor"])
                self.assertEqual(
                    self.admitted_tasks(prepared), self.admitted_tasks(again)
                )
                self.assertEqual(
                    {
                        k: v
                        for k, v in tools.items()
                        if k not in {"task", "cwd", "outputSchema"}
                    },
                    {
                        k: v
                        for k, v in self.descriptor(again)["launch"].items()
                        if k not in {"task", "cwd", "outputSchema"}
                    },
                )
                agent = (
                    Path(again["call"]["cwd"])
                    / ".pi/agents"
                    / (again["call"]["agent"] + ".md")
                )
                first = (
                    Path(prepared["call"]["cwd"])
                    / ".pi/agents"
                    / (prepared["call"]["agent"] + ".md")
                )
                self.assertEqual(
                    [
                        line
                        for line in first.read_text().splitlines()
                        if line.startswith("tools:")
                    ],
                    [
                        line
                        for line in agent.read_text().splitlines()
                        if line.startswith("tools:")
                    ],
                )
                self.command(again, "invalidate", {})

    @verifies("scenario.implementation.missing-tasks")
    def test_no_task_list_is_refused_before_a_programmer(self):
        self.update(lambda s: s.update(tasks=[]))
        value = self.prepare()
        self.assertEqual("rejected", value["state"], value)
        self.assertEqual({"missing_tasks"}, codes(value))
        self.assert_no_call(value)
        self.assertEqual([], self.state()["tasks"])


class ComponentWorkTests(Candidate, unittest.TestCase):
    tasks = (local_task(), local_task("task.ledger-entry", COMPONENT))

    def component_tasks(self):
        return [task for task in self.tasks if task["target_id"] == COMPONENT]

    @verifies("scenario.implementation.caller-components")
    def test_component_work_returns_as_a_typed_field(self):
        value = self.prepare()
        self.assertEqual("not-run", value["state"], value)
        self.assertFalse(value["accepted"])
        data = value["result"]["output"]["data"]
        self.assertEqual("unsupported", data["outcome"])
        self.assertEqual(
            [
                {
                    "target_id": COMPONENT,
                    "task": component_intent(self.component_tasks()),
                }
            ],
            data["components"],
        )
        self.assert_no_call(value)
        self.assert_no_completion()

    @verifies("scenario.implementation.components-current")
    def test_current_component_work_lets_the_local_programmer_run(self):
        self.complete_component(self.component_tasks())
        prepared = self.prepare()
        self.assertEqual("prepared", prepared["state"], prepared)
        self.assertEqual([self.tasks[0]], self.admitted_tasks(prepared))
        value = self.run_programmer(prepared)
        self.assertTrue(value["accepted"], value)
        state = self.state()
        self.assertTrue(all(task["complete"] for task in state["tasks"]))
        repository = self.repository()
        ledger = repository.module(COMPONENT)
        self.assertEqual(
            {
                COMPONENT: {
                    "spec": target_revision(repository, ledger),
                    "implementation": implementation_digest(repository, ledger),
                }
            },
            state["component_revisions"],
        )

    @verifies("scenario.implementation.components-stale")
    def test_changed_component_code_returns_the_component_again(self):
        self.complete_component(self.component_tasks())
        before = set(self.calls.iterdir())
        (self.root / "app/ledger.py").write_text("# changed after component work\n")
        value = self.prepare()
        self.assertEqual("not-run", value["state"], value)
        data = value["result"]["output"]["data"]
        self.assertEqual("unsupported", data["outcome"])
        self.assertEqual(
            [
                {
                    "target_id": COMPONENT,
                    "task": component_intent(self.component_tasks()),
                }
            ],
            data["components"],
        )
        self.assert_no_call(value, before)
        self.assert_no_completion()

    @verifies("scenario.implementation.components-context-stale")
    def test_a_changed_component_spec_in_the_owner_context_makes_the_plan_stale(self):
        self.complete_component(self.component_tasks())
        before = set(self.calls.iterdir())
        entry = self.root / "specs/ledger/module.md"
        entry.write_text(entry.read_text() + "\nThe ledger also records reversals.\n")
        value = self.prepare()
        self.assertEqual("rejected", value["state"], value)
        self.assertEqual({"stale_context"}, codes(value))
        self.assertIsNone(value["result"]["output"], value)
        self.assert_no_call(value, before)
        self.assert_no_completion()


class ConsumerComponentTests(Candidate, unittest.TestCase):
    """The component is a consumer of the owner, so its Spec is outside the owner's context."""

    tasks = (local_task(), local_task("task.bank-route", "scope.bank"))

    def write_project(self, root):
        project(root)
        metadata = json.loads((root / "specs/bank/module.md.json").read_text())
        metadata["defines"].append(
            {
                "id": "realization.bank.router",
                "type": "realization",
                "title": "Request router",
                "meaning": "#realization.bank.router",
                "entries": ["app/bank.py"],
                "pending": [],
            }
        )
        (root / "specs/bank/module.md.json").write_text(json.dumps(metadata, indent=2))
        entry = root / "specs/bank/module.md"
        entry.write_text(
            entry.read_text().replace(
                "## Relationships",
                '<a id="realization.bank.router"></a>\n\n'
                "Routes each transfer request to the transfer Module.\n\n"
                "## Relationships",
            )
        )
        (root / "app/bank.py").write_text("def route(request):\n    return request\n")

    @verifies("scenario.implementation.components-stale")
    def test_changed_component_spec_returns_the_component_again(self):
        component = [task for task in self.tasks if task["target_id"] == "scope.bank"]
        self.complete_component(component, "scope.bank", "app/bank.py")
        before = set(self.calls.iterdir())
        entry = self.root / "specs/bank/module.md"
        entry.write_text(entry.read_text() + "\nBanking also routes refunds.\n")
        value = self.prepare()
        self.assertEqual("not-run", value["state"], value)
        data = value["result"]["output"]["data"]
        self.assertEqual("unsupported", data["outcome"])
        self.assertEqual(
            [{"target_id": "scope.bank", "task": component_intent(component)}],
            data["components"],
        )
        self.assert_no_call(value, before)
        self.assert_no_completion()


class ComponentOnlyTests(Candidate, unittest.TestCase):
    tasks = (local_task("task.ledger-entry", COMPONENT),)

    @verifies("scenario.implementation.components-only")
    def test_only_current_component_work_needs_no_programmer(self):
        self.complete_component(list(self.tasks))
        value = self.prepare()
        self.assertEqual("not-run", value["state"], value)
        self.assertTrue(value["accepted"])
        self.assertEqual("succeeded", value["result"]["status"], value)
        self.assertNotIn("call", value)
        state = self.state()
        self.assertEqual(
            [{**task, "complete": True} for task in self.tasks], state["tasks"]
        )
        self.assertEqual(
            ("implementation", "completed"), (state["phase"], state["status"])
        )
        self.assertIn(COMPONENT, state["component_revisions"])


class SharedFileTests(Candidate, unittest.TestCase):
    task = SHARED_TASK
    tasks = (local_task("task.adapt", "module.a"),)

    def write_project(self, root):
        fixture = SharedFileFixture(self)
        fixture.root = root
        # SharedFileProject.setUp writes into its own temporary directory; point it at ``root``.
        with patch.object(tempfile, "TemporaryDirectory") as directory:
            directory.return_value.name = str(root)
            fixture.setUp()

    @verifies("scenario.implementation.shared-file")
    def test_a_programmer_of_a_shared_file_is_bound_to_every_binder(self):
        prepared = self.prepare()
        self.assertEqual("prepared", prepared["state"], prepared)
        snapshot = self.descriptor(prepared)["snapshot"]
        self.assertEqual(
            ["module.b"], [item["module_id"] for item in snapshot["shared_bindings"]]
        )
        index = self.index(prepared)
        documents = {source["path"] for source in index["spec_resolution"]["sources"]}
        shared = {
            source["path"]
            for binding in index["shared_bindings"]
            for source in binding["spec_resolution"]["sources"]
        }
        self.assertIn("specs/a/module.md", documents)
        self.assertIn("specs/b/module.md", shared)
        self.assertEqual(
            sorted(
                str(self.root / path) for path in ("source/a.py", "source/shared.py")
            ),
            sorted(index["intended_write_paths"]),
        )
        self.command(prepared, "invalidate", {})
