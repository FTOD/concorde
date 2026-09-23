"""A primary worktree with one linked candidate of the transfer fixture project.

``WorktreeProject`` is a ``unittest.TestCase`` mixin: ``setUp`` commits the fixture project in a
primary worktree on branch ``integration`` and adds the candidate worktree ``change``; the helpers
run capabilities, relay in process, validate a ready candidate and declare pending files.
"""

import json
import subprocess

import tempfile
from pathlib import Path

from concorde.harness import change_worktree, configure
from concorde.harness.change_worktree import git, git_value, read_change
from concorde.harness.host import OperationHost
from concorde.operations.dispatch import run_operation
from concorde.spec.typed_data import typed

from .spec_project import CONFIGURATION, PACKAGE, project


class WorktreeProject:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.primary = self.directory / "primary"
        self.primary.mkdir()
        project(self.primary)
        (self.primary / "AGENTS.md").write_text(
            "# Existing project policy\nKeep project conventions.\n"
        )
        (self.primary / "shared.txt").write_text("base\n")
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        self.commit(self.primary, "Fixture")
        self.change = self.directory / "change"
        git(self.primary, "worktree", "add", "-b", "candidate", str(self.change))
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the transfer contract",
        }

    def state_file(self):
        return next(
            (self.primary / ".concorde/status").glob("change.*.json"),
            self.primary / ".concorde/status/missing.json",
        )

    def commit(self, root, message):
        git(root, "add", "-A")
        git(root, "commit", "-qm", message)
        return git_value(root, "rev-parse", "HEAD")

    def call_operation(self, root, name, data, *, host=None, mode="execute"):
        host = host or OperationHost(root, PACKAGE, mode=mode)
        return run_operation(
            name, CONFIGURATION, typed(name + "-request", data), host_context=host
        )

    def ready_delivery(self):
        """A directly validated candidate for tests focused on Git delivery transactions."""
        (self.change / "app/transfer.py").write_text(
            "def transfer(balance, amount):\n"
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            "    return balance - amount\n"
        )
        # Validation needs a registered change; the user session registers the candidate.
        change_worktree.ensure_change(self.change, task=self.task)
        result = self.call_operation(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        return read_change(self.change, required=True)["change_id"]

    def tree_bytes(self, tree, path):
        return subprocess.run(
            ["git", "-C", str(self.change), "show", f"{tree}:{path}"],
            capture_output=True,
            check=True,
        ).stdout

    def relay_in_process(self):
        """A trusted relay running the candidate in this process."""
        self.relayed = []

        def relay(host, operation, invocation, candidate):
            inner = OperationHost(candidate, PACKAGE, mode=invocation["mode"])
            result = run_operation(
                operation, CONFIGURATION, invocation["input"], host_context=inner
            )
            self.relayed.append(
                {
                    "operation": operation,
                    "invocation": invocation,
                    "candidate": candidate,
                    "result": result,
                }
            )
            return result, ""

        return relay

    def primary_host(self, relay):
        return OperationHost(self.primary, PACKAGE, relay=relay)

    def remove_candidate(self, created):
        git(self.primary, "worktree", "remove", "--force", str(created))
        created.parent.rmdir()

    def configure_request(self, **extra):
        selection = typed(
            "concorde-operation-configuration",
            {"model": "openai-codex/gpt-6-astra", "thinking": "high"},
        )
        proposed = configure.propose(self.primary, PACKAGE, selection)["data"]
        return selection, {
            "action": "apply",
            "proposal": proposed["proposal"],
            "proposal_digest": proposed["proposal_digest"],
            **extra,
        }

    def stored_configuration(self, root):
        value = json.loads((root / ".concorde/config.json").read_text())
        return value["operation_configuration"]

    def declare_pending_files(self):
        """Declare two files the plan intends to create, before any of them exists."""
        path = self.change / "specs/transfer/module.md.json"
        metadata = json.loads(path.read_text())
        realizations = [
            item for item in metadata["defines"] if item["type"] == "realization"
        ]
        realizations[0].update(
            entries=["app/rounding.py", "app/transfer.py"], pending=["app/rounding.py"]
        )
        realizations[1].update(
            entries=["checks/rounding_check.py", "checks/transfer_check.py"],
            pending=["checks/rounding_check.py"],
        )
        path.write_text(json.dumps(metadata, indent=2) + "\n")
