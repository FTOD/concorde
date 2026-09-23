"""pytest plugin: test reasons, measured input identity and nested runtime diagnostics.

The rootdir ``conftest.py`` loads this plugin, so ``.venv/bin/python -m pytest`` needs no extra
flag. pytest-xdist schedules the collected ``unittest`` cases across worker processes; this
plugin keeps the evidence the retired subprocess runner recorded:

- ``--reason``, ``--scope``, ``--phase``, ``--attempt`` and ``--prior`` declare why a run happens
  and what it repeats; legacy callers pass none of them and get ``manual``/``unspecified``;
- ``--json=PATH`` writes one summary with whitelisted input/test/runtime/lock/environment
  fingerprints, per-unit queue/execution intervals, discovery/total intervals and layer "C" spans;
- every process that executes tests gets its own ``CONCORDE_DIAGNOSTIC_TIMING_DIR`` and each unit
  its own subdirectory, so runtime spans written by ``concorde.harness.timing.timed`` fixtures are
  nested under the unit that produced them and the controller aggregates them from the workers.

Pass values with ``=`` (``--json=PATH``, ``--prior=PATH``): pytest chooses its rootdir from the
bare arguments before any conftest plugin has registered options, so a space-separated value
that exists as a path (a prior summary always does) would move the rootdir there and lose this
configuration.

A unit is one collected test. Its queue interval is measured against the collection end of the
process that ran it; clocks of different processes are never subtracted. Fixture setup stays
unknown unless runtime spans measure it: ``unittest.setUp`` runs inside pytest's call phase, so
the observed pytest phase durations are reported separately and never as setup time.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.concorde.support.paths import REPOSITORY_ROOT

ROOT = REPOSITORY_ROOT
TIMING_DIR = "CONCORDE_DIAGNOSTIC_TIMING_DIR"
REASONS = (
    "manual",
    "local-edit",
    "coherent-change",
    "stable-final",
    "changed-input",
    "failure",
    "independent",
    "bootstrap",
)
SCOPES = ("unspecified", "targeted", "full")
PHASES = ("unspecified", "maintenance", "tester", "postcommit")
TIMING_NOTE = (
    "Execution includes imports and fixtures; setup is unknown unless runtime spans measure it, "
    "and observed pytest phase durations are reported separately. Runtime fixture spans are "
    "nested, never additive wall time. Unit time is summed concurrent work, not elapsed wall "
    "time. Critical unit is last to finish, not a dependency-graph proof."
)

# Scheduling hint only: node-id prefixes of the units whose own duration would otherwise decide
# when the parallel batch ends, longest first. They are collected first, interleaved with short
# units, so that xdist's load scheduler (initial chunks of two, then one unit at a time with
# --maxschedchunk 1) starts each on its own worker immediately. Correctness never depends on it;
# an outdated entry only costs wall time. Prefer fixing a slow test over extending this list.
HEAVY: tuple[str, ...] = (
    "tests/concorde/distribution/test_local_installation.py::LocalInstallationTests::"
    "test_source_and_installed_provider_supply_independent_git_worktree_installs",
    "tests/concorde/harness/test_tester_tmp.py::",
    "tests/concorde/spec/test_distribution.py::",
    "tests/concorde/delivery/test_deliver.py::",
    "tests/concorde/distribution/test_install_concorde.py::",
    "tests/concorde/spec/test_module_model.py::",
)


@dataclass
class Unit:
    """One collected test executed by one process."""

    nodeid: str
    module: str
    worker: str
    process_id: int
    status: str = "pending"
    queued_ns: int | None = None
    started_ns: int | None = None
    ended_ns: int | None = None
    started_at: str | None = None
    ended_at: str | None = None
    queue_seconds: float | None = None
    setup_seconds: float | None = None
    execution_seconds: float | None = None
    phase_seconds: dict[str, float] = field(default_factory=dict)
    runtime_spans: list[dict] = field(default_factory=list)
    telemetry_complete: bool = True

    @property
    def seconds(self) -> float:
        return self.execution_seconds or 0.0

    @property
    def failed(self) -> bool:
        return self.status in {"failed", "error"}


def module_name(nodeid: str) -> str:
    path = nodeid.split("::", 1)[0]
    return path[:-3].replace("/", ".") if path.endswith(".py") else path


def prioritize(items: list) -> list:
    """Heavy units first, one between every two short ones; order is otherwise preserved."""
    ranked = []
    light = []
    for index, item in enumerate(items):
        for rank, prefix in enumerate(HEAVY):
            if item.nodeid.startswith(prefix):
                ranked.append((rank, index, item))
                break
        else:
            light.append(item)
    if not ranked:
        return items
    heavy = [item for _, _, item in sorted(ranked, key=lambda entry: entry[:2])]
    ordered = []
    for index, item in enumerate(heavy):
        ordered.append(item)
        if index < len(light):
            ordered.append(light[index])
    return ordered + light[len(heavy) :]


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def fingerprint(tests: list[str]) -> dict:
    """Whitelisted input membership and nonsecret runtime facts, not ambient env serialization."""
    complete = True
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=ROOT,
            capture_output=True,
            timeout=10,
        )
        complete = listing.returncode == 0
        files = listing.stdout.decode().split("\0") if complete else []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        complete, files = False, []
    prefixes = (
        "src/",
        "scripts/",
        "tests/",
        "prompts/",
        "protocol/",
        "specs/",
        ".concorde/protocol/",
    )
    exact = {
        "AGENTS.md",
        "concorde.json",
        "pyproject.toml",
        "uv.lock",
        ".concorde/config.json",
        ".concorde/specs.json",
    }
    entries = {}
    for name in sorted(set(files)):
        if name in exact or name.startswith(prefixes):
            path = ROOT / name
            if path.is_file() and not path.is_symlink():
                try:
                    entries[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError:
                    complete = False
    try:
        runtime = {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "pytest": importlib.metadata.version("pytest"),
        }
    except importlib.metadata.PackageNotFoundError:
        runtime = None
    environment = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "bytecode_disabled": os.environ.get("PYTHONDONTWRITEBYTECODE") == "1",
    }
    parts = {
        "input": digest(entries) if complete else None,
        "tests": digest(sorted(tests)),
        "runtime": digest(runtime),
        "lock": digest(
            {k: v for k, v in entries.items() if k.endswith(("lock", "lock.json"))}
        ),
        "environment": digest(environment),
    }
    return {
        "digest": digest(parts),
        **parts,
        "runtime_facts": runtime,
        "environment_facts": environment,
        "environment_complete": False,
        "files": len(entries),
        "input_complete": complete,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConcordeTiming:
    """Per-process unit timing; the controller (or the single process) also aggregates."""

    def __init__(self, config: pytest.Config):
        self.config = config
        workerinput = getattr(config, "workerinput", None)
        self.worker = workerinput["workerid"] if workerinput else "main"
        self.controller = workerinput is None
        self.started_ns = time.monotonic_ns()
        self.started_at = utc_now()
        self.discovery_ended_ns: int | None = None
        self.previous_directory = os.environ.get(TIMING_DIR)
        self.directory = Path(
            tempfile.mkdtemp(prefix=f"concorde-test-timing-{self.worker}-")
        ).resolve()
        os.environ[TIMING_DIR] = str(self.directory)
        self.active: dict[str, tuple[Unit, Path]] = {}
        self.counter = 0
        self.units: dict[str, Unit] = {}
        self.categories: dict[str, list[str]] = {}
        self.phases: dict[str, dict[str, float]] = {}
        self.collected: list[str] = []
        self.summary: dict | None = None
        self.messages: list[str] = []

    # -- every process -------------------------------------------------------------------------

    def pytest_unconfigure(self) -> None:
        if self.previous_directory is None:
            os.environ.pop(TIMING_DIR, None)
        else:
            os.environ[TIMING_DIR] = self.previous_directory
        shutil.rmtree(self.directory, ignore_errors=True)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, items: list) -> None:
        items[:] = prioritize(items)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.discovery_ended_ns = time.monotonic_ns()
        self.collected = [item.nodeid for item in session.items]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item: pytest.Item):
        self.counter += 1
        scratch = self.directory / str(self.counter)
        scratch.mkdir()
        os.environ[TIMING_DIR] = str(scratch)
        unit = Unit(item.nodeid, module_name(item.nodeid), self.worker, os.getpid())
        unit.queued_ns = self.discovery_ended_ns
        unit.started_ns = time.monotonic_ns()
        unit.started_at = utc_now()
        unit.queue_seconds = (
            (unit.started_ns - unit.queued_ns) / 1e9
            if unit.queued_ns is not None
            else None
        )
        self.active[item.nodeid] = (unit, scratch)
        try:
            yield
        finally:
            self.active.pop(item.nodeid, None)
            os.environ[TIMING_DIR] = str(self.directory)
            shutil.rmtree(scratch, ignore_errors=True)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call):
        outcome = yield
        if call.when != "teardown" or item.nodeid not in self.active:
            return
        report = outcome.get_result()
        unit, scratch = self.active[item.nodeid]
        unit.ended_ns = time.monotonic_ns()
        unit.ended_at = utc_now()
        unit.execution_seconds = (unit.ended_ns - unit.started_ns) / 1e9
        for path in sorted(scratch.glob("*.json")):
            try:
                trace = json.loads(path.read_text())
                unit.runtime_spans.extend(trace["spans"])
                unit.telemetry_complete &= bool(trace["complete"])
            except (OSError, ValueError, KeyError, TypeError):
                unit.telemetry_complete = False
        if any(
            "CONCORDE_TIMING_INCOMPLETE" in content
            for key, content in report.sections
            if "stderr" in key
        ):
            unit.telemetry_complete = False
        # Travels with the teardown report to the xdist controller (reports keep extra fields).
        report.concorde_unit = {
            key: value for key, value in asdict(unit).items() if key != "phase_seconds"
        }

    # -- controller, or the single process without xdist ---------------------------------------

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, ids) -> None:
        self.discovery_ended_ns = time.monotonic_ns()
        self.collected = list(ids)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if not self.controller:
            return
        category = self.config.hook.pytest_report_teststatus(
            report=report, config=self.config
        )[0]
        categories = self.categories.setdefault(report.nodeid, [])
        # Passed phases and passed subtests carry no verdict of their own.
        if category and not category.startswith("subtests"):
            categories.append(category)
        self.phases.setdefault(report.nodeid, {})[report.when] = report.duration
        recorded = getattr(report, "concorde_unit", None)
        if recorded is not None:
            unit = Unit(**recorded)
            unit.status = next(
                (c for c in categories if c != "passed"), "passed" if categories else ""
            )
            unit.phase_seconds = self.phases.pop(report.nodeid)
            self.units[report.nodeid] = unit

    def pytest_sessionfinish(self, exitstatus) -> None:
        if not self.controller or self.config.option.collectonly:
            return
        option = self.config.option
        if option.concorde_json or option.prior:
            self.summary = self.build_summary(int(exitstatus))
            if option.concorde_json:
                Path(option.concorde_json).write_text(
                    json.dumps(self.summary, indent=2) + "\n"
                )
        workers = getattr(option, "numprocesses", None) or 0
        self.messages.append(
            f"reason={option.reason} scope={option.scope} phase={option.phase} "
            f"attempt={option.attempt} workers={workers or 'in-process'}"
            + (f" dist={option.dist}" if workers else "")
        )
        elapsed = (time.monotonic_ns() - self.started_ns) / 1e9
        discovery = (
            f"{(self.discovery_ended_ns - self.started_ns) / 1e9:.1f}s"
            if self.discovery_ended_ns is not None
            else "unknown"
        )
        unit_seconds = sum(unit.seconds for unit in self.units.values())
        self.messages.append(
            f"discovery {discovery}, elapsed {elapsed:.1f}s; unit time {unit_seconds:.1f}s "
            "is summed concurrent work, not wall time"
        )
        if self.summary is not None and self.summary["same_declared_inputs"]:
            self.messages.append(
                f"same declared inputs as prior run; rerun reason: {option.reason} "
                "(environment coverage is partial)"
            )
        if option.concorde_json:
            self.messages.append(f"summary written to {option.concorde_json}")

    def pytest_terminal_summary(self, terminalreporter) -> None:
        if not self.messages:
            return
        terminalreporter.write_sep("-", "concorde test evidence")
        for message in self.messages:
            terminalreporter.write_line(message)

    def build_summary(self, exitstatus: int) -> dict:
        from concorde.harness.timing import interval_record

        option = self.config.option
        prior = json.loads(Path(option.prior).read_text()) if option.prior else None
        inputs = fingerprint(self.collected)
        same_input = (
            prior.get("fingerprint", {}).get("digest") == inputs["digest"]
            if prior
            and inputs["input_complete"]
            and inputs["runtime_facts"] is not None
            else None
        )
        units = sorted(self.units.values(), key=lambda unit: -unit.seconds)
        run_id = str(uuid.uuid4())
        ended_ns = time.monotonic_ns()
        failed = exitstatus != 0 or any(unit.failed for unit in units)
        total_span = interval_record(
            name="test.total",
            trace_id=run_id,
            started_at=self.started_at,
            start_ns=self.started_ns,
            end_ns=ended_ns,
            status="error" if failed else "ok",
        )
        spans = [
            total_span,
            interval_record(
                name="test.discovery",
                trace_id=run_id,
                parent_id=total_span["span_id"],
                started_at=self.started_at,
                start_ns=self.started_ns,
                end_ns=self.discovery_ended_ns,
                status="ok" if self.discovery_ended_ns is not None else "incomplete",
            ),
        ]
        for unit in units:
            spans.append(
                {
                    **interval_record(
                        name="test.unit",
                        trace_id=run_id,
                        parent_id=total_span["span_id"],
                        started_at=unit.started_at,
                        start_ns=unit.started_ns,
                        end_ns=unit.ended_ns,
                        status="error" if unit.failed else "ok",
                    ),
                    "process_id": unit.process_id,
                }
            )
        counts = {
            key: sum(1 for unit in units if unit.status == key)
            for key in ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
        }
        workers = getattr(option, "numprocesses", None) or 0
        totals = {
            "tests": len(units),
            "collected": len(self.collected),
            **counts,
            "modules": len({unit.module for unit in units}),
            "failed_units": sum(1 for unit in units if unit.failed),
            "workers": len({unit.worker for unit in units}),
            "wall_seconds": round((ended_ns - self.started_ns) / 1e9, 2),
            "unit_seconds": round(sum(unit.seconds for unit in units), 2),
        }
        critical = max(units, key=lambda unit: unit.ended_at or "", default=None)
        return {
            "schema_version": 3,
            "run_id": run_id,
            "spans": spans,
            "reason": option.reason,
            "scope": option.scope,
            "phase": option.phase,
            "attempt": option.attempt,
            "prior_run_id": prior.get("run_id") if prior else None,
            "same_declared_inputs": same_input,
            "fingerprint": inputs,
            "started_at": self.started_at,
            "discovery_seconds": (
                (self.discovery_ended_ns - self.started_ns) / 1e9
                if self.discovery_ended_ns is not None
                else None
            ),
            "elapsed_seconds": (ended_ns - self.started_ns) / 1e9,
            "critical_unit": critical.nodeid if critical else None,
            "timing_note": TIMING_NOTE,
            "python": sys.executable,
            "distribution": getattr(option, "dist", "no") if workers else "no",
            "exit_status": exitstatus,
            "totals": totals,
            "units": [asdict(unit) for unit in units],
        }


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup(
        "concorde", "Concorde test evidence (pass values as --option=value)"
    )
    group.addoption(
        "--reason",
        choices=REASONS,
        default="manual",
        help="why this run happens (default: manual)",
    )
    group.addoption(
        "--scope", choices=SCOPES, default="unspecified", help="declared test scope"
    )
    group.addoption(
        "--phase",
        choices=PHASES,
        default="unspecified",
        help="declared lifecycle phase",
    )
    group.addoption(
        "--attempt", type=int, default=1, help="positive attempt number (default: 1)"
    )
    group.addoption(
        "--prior",
        default=None,
        metavar="PATH",
        help="--prior=PATH: JSON summary of a prior run to compare declared inputs against",
    )
    group.addoption(
        "--json",
        dest="concorde_json",
        default=None,
        metavar="PATH",
        help="--json=PATH: write a JSON summary of every unit, fingerprints and spans",
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.option.attempt < 1:
        raise pytest.UsageError("--attempt must be positive")
    config.pluginmanager.register(ConcordeTiming(config), "concorde-timing")
