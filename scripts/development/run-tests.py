#!/usr/bin/env python3
"""Run the Python test suite as one subprocess per test module, in parallel.

``python -m unittest discover -s tests/concorde -t . -p 'test_*.py'`` runs the modules under
``tests/concorde`` one after another and takes about six minutes; nearly all of that time is spent
in a handful of modules that build packages, create git worktrees or provision virtual environments
in temporary directories. This runner discovers the same modules and runs each one in its own
interpreter (``<python> -m unittest <module>`` from the repository root), so the wall-clock time
approaches that of the slowest unit instead of the sum. Modules listed in ``FAN_OUT`` are split
further, one subprocess per test method, because one such module would otherwise dominate the
batch; modules listed in ``SERIAL`` run one at a time after the parallel batch.

The serial discover command remains valid; this script only changes how the same modules are
scheduled. It uses the standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import tempfile
import uuid
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = ROOT / "tests" / "concorde"
TEST_PACKAGE = "tests.concorde"

# Modules that must not share the machine with other test processes, with the reason. They run one
# at a time after the parallel batch. Prefer fixing a test to use its own temporary state over
# adding it here.
SERIAL: dict[str, str] = {}

# Modules whose own duration would dominate the parallel batch even though their tests are
# independent. Each is fanned out one subprocess per test method; every part repeats the module
# import and class fixtures, which costs far less than the module's total time. Skipped with
# --sequential.
FAN_OUT: frozenset[str] = frozenset(
    {
        "tests.concorde.operations.test_review",
        "tests.concorde.distribution.test_install_concorde",
        "tests.concorde.harness.test_worktree_lifecycle",
        "tests.concorde.spec.test_module_model",
    }
)

# Enumerates the test ids of one module inside the test interpreter, so fan-out uses the loader's
# own view (inherited tests, skip decorators, load failures) instead of a source-level guess.
LIST_TESTS = """
import sys, unittest

def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item

for test in flatten(unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])):
    print(test.id())
"""

RAN_PATTERN = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.MULTILINE)
RESULT_PATTERN = re.compile(r"^(OK|FAILED)(?: \((.*)\))?$", re.MULTILINE)


@dataclass
class Unit:
    """One ``python -m unittest <target>`` invocation."""

    module: str
    target: str
    serial: bool = False
    seconds: float = 0.0
    returncode: int | None = None
    output: str = ""
    status: str = "pending"
    tests: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    expected_failures: int = 0
    unexpected_successes: int = 0
    queued_ns: int | None = None
    started_ns: int | None = None
    ended_ns: int | None = None
    started_at: str | None = None
    queue_seconds: float | None = None
    setup_seconds: float | None = None
    execution_seconds: float | None = None
    runtime_spans: list[dict] = field(default_factory=list)
    telemetry_complete: bool = True

    @property
    def part(self) -> str:
        return self.target[len(self.module) + 1 :] if self.target != self.module else ""

    @property
    def failed(self) -> bool:
        return self.status != "ok"


@dataclass
class ModuleReport:
    module: str
    units: list[Unit] = field(default_factory=list)

    @property
    def wall(self) -> float:
        return max((unit.seconds for unit in self.units), default=0.0)

    @property
    def total(self) -> float:
        return sum(unit.seconds for unit in self.units)

    @property
    def failed(self) -> bool:
        return any(unit.failed for unit in self.units)


def discover_modules() -> list[str]:
    """Return the dotted names of every ``tests/concorde/<package>/test_*.py`` module."""

    modules = []
    for path in sorted(TESTS_ROOT.glob("*/test_*.py")):
        if not (path.parent / "__init__.py").is_file():
            continue
        modules.append(f"{TEST_PACKAGE}.{path.parent.name}.{path.stem}")
    return modules


def module_path(module: str) -> Path:
    return ROOT / (module.replace(".", "/") + ".py")


def choose_interpreter(explicit: str | None) -> str:
    """Prefer the checkout's ``.venv`` so ``python3 scripts/development/run-tests.py`` works."""

    if explicit:
        return explicit
    for candidate in (ROOT / ".venv/bin/python", ROOT / ".venv/Scripts/python.exe"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def list_tests(python: str, module: str) -> list[str] | None:
    """Return the module's test ids, or ``None`` when the loader cannot import it."""

    completed = subprocess.run(
        [python, "-c", LIST_TESTS, module], cwd=ROOT, capture_output=True, text=True
    )
    ids = completed.stdout.split()
    if (
        completed.returncode
        or not ids
        or any(not test.startswith(module + ".") for test in ids)
    ):
        return None
    return ids


def run_unit(python: str, unit: Unit) -> Unit:
    started = time.perf_counter()
    unit.started_ns = time.monotonic_ns()
    unit.started_at = datetime.now(timezone.utc).isoformat()
    unit.queue_seconds = (
        (unit.started_ns - unit.queued_ns) / 1e9 if unit.queued_ns is not None else None
    )
    with tempfile.TemporaryDirectory(prefix="concorde-test-timing-") as directory:
        completed = subprocess.run(
            [python, "-m", "unittest", unit.target],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            env={**os.environ, "CONCORDE_DIAGNOSTIC_TIMING_DIR": directory},
        )
        unit.ended_ns = time.monotonic_ns()
        unit.execution_seconds = (unit.ended_ns - unit.started_ns) / 1e9
        for path in sorted(Path(directory).glob("*.json")):
            try:
                trace = json.loads(path.read_text())
                unit.runtime_spans.extend(trace["spans"])
                unit.telemetry_complete &= trace["complete"]
            except (OSError, ValueError, KeyError):
                unit.telemetry_complete = False
    unit.seconds = time.perf_counter() - started
    unit.returncode = completed.returncode
    unit.output = completed.stdout
    if "CONCORDE_TIMING_INCOMPLETE" in unit.output:
        unit.telemetry_complete = False
    parse_summary(unit)
    return unit


def parse_summary(unit: Unit) -> None:
    ran = RAN_PATTERN.findall(unit.output)
    result = RESULT_PATTERN.findall(unit.output)
    if ran and result:
        unit.tests = int(ran[-1])
        verdict, details = result[-1]
        counts = {
            key.strip(): int(value)
            for key, value in re.findall(r"([a-z ]+)=(\d+)", details)
        }
        unit.failures = counts.get("failures", 0)
        unit.errors = counts.get("errors", 0)
        unit.skipped = counts.get("skipped", 0)
        unit.expected_failures = counts.get("expected failures", 0)
        unit.unexpected_successes = counts.get("unexpected successes", 0)
        if verdict == "OK" and unit.returncode == 0 and unit.tests:
            unit.status = "ok"
        elif unit.failures or unit.unexpected_successes:
            unit.status = "FAIL"
        else:
            unit.status = "ERROR"
    else:
        # No unittest summary: an import failure, a crash or an unexpected exit.
        unit.status = "ERROR"
        unit.errors = max(unit.errors, 1)


def describe(unit: Unit) -> str:
    detail = f"{unit.tests} test{'s' if unit.tests != 1 else ''}"
    if unit.failures:
        detail += f", {unit.failures} failure{'s' if unit.failures != 1 else ''}"
    if unit.errors:
        detail += f", {unit.errors} error{'s' if unit.errors != 1 else ''}"
    if unit.skipped:
        detail += f", {unit.skipped} skipped"
    if unit.returncode not in (0, 1):
        detail += f", exit {unit.returncode}"
    return detail


def print_completion(index: int, total: int, unit: Unit) -> None:
    label = unit.target if not unit.serial else unit.target + "  [serial]"
    print(
        f"[{index:>{len(str(total))}}/{total}] {unit.status:<5} {unit.seconds:7.1f}s  {label}  ({describe(unit)})",
        flush=True,
    )
    if unit.failed:
        rule = "-" * 20
        print(f"{rule} output of {unit.target} {rule}")
        print(unit.output.rstrip("\n"))
        print(f"{rule} end of {unit.target} {rule}", flush=True)


def build_units(
    modules: list[str], python: str, fan_out: bool, jobs: int
) -> list[Unit]:
    """Expand the selected modules into units, fanning out the listed modules per test method."""

    fanned = [
        module
        for module in modules
        if fan_out and module in FAN_OUT and module not in SERIAL
    ]
    listings: dict[str, list[str] | None] = {}
    if fanned:
        with ThreadPoolExecutor(max_workers=min(jobs, len(fanned))) as pool:
            for module, ids in zip(
                fanned, pool.map(lambda name: list_tests(python, name), fanned)
            ):
                listings[module] = ids
    units: list[Unit] = []
    for module in modules:
        if module in SERIAL:
            continue
        ids = listings.get(module)
        if ids:
            units.extend(Unit(module, test) for test in ids)
        else:
            units.append(Unit(module, module))
    if fan_out:
        # Start the presumably slowest work first: fanned-out parts, then larger modules.
        units.sort(
            key=lambda unit: (
                unit.target == unit.module,
                -module_path(unit.module).stat().st_size,
                unit.target,
            )
        )
    return units


def print_report(
    reports: list[ModuleReport], units: list[Unit], wall: float, jobs: int
) -> dict:
    print()
    print(
        "Modules by wall-clock time (fanned-out modules show their longest part and the sum of parts):"
    )
    ordered = sorted(reports, key=lambda report: (-report.wall, report.module))
    for report in ordered:
        status = "FAIL" if report.failed else "ok"
        parts = ""
        if len(report.units) > 1:
            parts = f"  [{len(report.units)} parts, sum {report.total:.1f}s]"
        elif report.units and report.units[0].serial:
            parts = "  [serial]"
        tests = sum(unit.tests for unit in report.units)
        print(
            f"  {report.wall:7.1f}s  {status:<5} {report.module}  ({tests} tests){parts}"
        )
    totals = {
        "tests": sum(unit.tests for unit in units),
        "failures": sum(unit.failures + unit.unexpected_successes for unit in units),
        "errors": sum(unit.errors for unit in units),
        "skipped": sum(unit.skipped for unit in units),
        "expected_failures": sum(unit.expected_failures for unit in units),
        "modules": len(reports),
        "subprocesses": len(units),
        "failed_units": sum(1 for unit in units if unit.failed),
        "jobs": jobs,
        "wall_seconds": round(wall, 2),
        "subprocess_seconds": round(sum(unit.seconds for unit in units), 2),
    }
    print()
    print(
        f"Ran {totals['tests']} tests in {totals['modules']} modules "
        f"({totals['subprocesses']} subprocesses, {jobs} jobs): "
        f"{totals['failures']} failures, {totals['errors']} errors, {totals['skipped']} skipped; "
        f"wall {wall:.1f}s, subprocess time {totals['subprocess_seconds']:.1f}s"
    )
    failed = [unit for unit in units if unit.failed]
    if failed:
        print("FAILED units:")
        for unit in failed:
            print(f"  {unit.status:<5} {unit.target}  ({describe(unit)})")
    else:
        print("OK")
    return totals


def fingerprint(python: str, modules: list[str]) -> dict:
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
        "agents/",
        "operations/",
        "prompts/",
        "protocol/",
        "specs/",
        "pi/",
        ".pi/agents/",
        ".pi/extensions/",
        ".concorde/protocol/",
    )
    exact = {
        "AGENTS.md",
        "concorde.json",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "package-lock.json",
        ".concorde/config.json",
        ".concorde/specs.json",
        ".pi/APPEND_SYSTEM.md",
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
    digest = lambda value: hashlib.sha256(
        json.dumps(value, sort_keys=True).encode()
    ).hexdigest()
    probe = subprocess.run(
        [
            python,
            "-I",
            "-c",
            "import sys,platform,importlib.metadata,json; print(json.dumps({'python':platform.python_version(),'implementation':platform.python_implementation(),'langgraph':importlib.metadata.version('langgraph')}))",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    runtime = json.loads(probe.stdout) if probe.returncode == 0 else None
    environment = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "bytecode_disabled": os.environ.get("PYTHONDONTWRITEBYTECODE") == "1",
        "studio_enabled": os.environ.get("CONCORDE_TEST_STUDIO") == "1",
    }
    parts = {
        "input": digest(entries) if complete else None,
        "tests": digest(modules),
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="parallel subprocesses (default: min(cpu_count, number of units))",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="run one module at a time without fan-out, like the discover command",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="SUBSTRING",
        help="only run modules whose dotted name or path contains SUBSTRING (repeatable)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        metavar="PATH",
        help="write a JSON summary of every unit to PATH",
    )
    parser.add_argument(
        "--python",
        default=None,
        metavar="PATH",
        help="interpreter for the subprocesses (default: .venv, else this interpreter)",
    )
    parser.add_argument(
        "--reason",
        choices=[
            "manual",
            "local-edit",
            "coherent-change",
            "stable-final",
            "changed-input",
            "failure",
            "independent",
            "bootstrap",
        ],
        default="manual",
    )
    parser.add_argument(
        "--scope", choices=["unspecified", "targeted", "full"], default="unspecified"
    )
    parser.add_argument(
        "--phase",
        choices=["unspecified", "maintenance", "tester", "postcommit"],
        default="unspecified",
    )
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--prior", type=Path)
    arguments = parser.parse_args(argv)
    if arguments.attempt < 1:
        parser.error("--attempt must be positive")
    discovery_started = time.monotonic_ns()
    run_started_at = datetime.now(timezone.utc).isoformat()

    python = choose_interpreter(arguments.python)
    modules = discover_modules()
    if arguments.filter:
        modules = [
            module
            for module in modules
            if any(
                needle in module or needle in str(module_path(module).relative_to(ROOT))
                for needle in arguments.filter
            )
        ]
    if not modules:
        print("no test modules matched", file=sys.stderr)
        return 2
    inputs = fingerprint(python, modules)
    prior = json.loads(arguments.prior.read_text()) if arguments.prior else None
    same_input = (
        prior.get("fingerprint", {}).get("digest") == inputs["digest"]
        if prior and inputs["input_complete"] and inputs["runtime_facts"] is not None
        else None
    )
    if same_input:
        print(
            f"Same declared inputs as prior run; rerun reason: {arguments.reason} (environment coverage is partial)"
        )
    cpu_count = os.cpu_count() or 1
    started = time.perf_counter()
    parallel = build_units(
        modules, python, fan_out=not arguments.sequential, jobs=cpu_count
    )
    serial = [
        Unit(module, module, serial=True) for module in modules if module in SERIAL
    ]
    total = len(parallel) + len(serial)
    if arguments.sequential:
        jobs = 1
    elif arguments.jobs is None:
        jobs = max(1, min(cpu_count, len(parallel)))
    else:
        jobs = max(1, arguments.jobs)
    fanned = sorted({unit.module for unit in parallel if unit.target != unit.module})
    print(
        f"Running {len(modules)} modules as {total} subprocesses with {jobs} job{'s' if jobs != 1 else ''} "
        f"using {python}"
    )
    if fanned:
        print(f"  fanned out per test method: {', '.join(fanned)}")
    if serial:
        print(
            f"  serial after the parallel batch: {', '.join(unit.module for unit in serial)}"
        )
    print(flush=True)

    discovery_ended = time.monotonic_ns()
    for unit in parallel + serial:
        unit.queued_ns = discovery_ended
    finished = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run_unit, python, unit) for unit in parallel]
        for future in as_completed(futures):
            finished += 1
            print_completion(finished, total, future.result())
    for unit in serial:
        finished += 1
        print_completion(finished, total, run_unit(python, unit))
    wall = time.perf_counter() - started

    units = parallel + serial
    reports: dict[str, ModuleReport] = {}
    for unit in units:
        reports.setdefault(unit.module, ModuleReport(unit.module)).units.append(unit)
    totals = print_report(list(reports.values()), units, wall, jobs)

    if arguments.json:
        sys.path.insert(0, str(ROOT / "src"))
        from concorde.harness.timing import interval_record

        run_id = str(uuid.uuid4())
        total_span = interval_record(
            name="test.total",
            trace_id=run_id,
            started_at=run_started_at,
            start_ns=discovery_started,
            end_ns=time.monotonic_ns(),
            status="error" if any(unit.failed for unit in units) else "ok",
        )
        spans = [
            total_span,
            interval_record(
                name="test.discovery",
                trace_id=run_id,
                parent_id=total_span["span_id"],
                started_at=run_started_at,
                start_ns=discovery_started,
                end_ns=discovery_ended,
            ),
        ]
        for unit in units:
            spans.append(
                interval_record(
                    name="test.unit",
                    trace_id=run_id,
                    parent_id=total_span["span_id"],
                    started_at=unit.started_at,
                    start_ns=unit.started_ns,
                    end_ns=unit.ended_ns,
                    status="error" if unit.failed else "ok",
                )
            )
        summary = {
            "schema_version": 2,
            "run_id": run_id,
            "spans": spans,
            "reason": arguments.reason,
            "scope": arguments.scope,
            "phase": arguments.phase,
            "attempt": arguments.attempt,
            "prior_run_id": prior.get("run_id") if prior else None,
            "same_declared_inputs": same_input,
            "fingerprint": inputs,
            "started_at": run_started_at,
            "discovery_seconds": (discovery_ended - discovery_started) / 1e9,
            "elapsed_seconds": (time.monotonic_ns() - discovery_started) / 1e9,
            "critical_unit": max(units, key=lambda u: u.ended_ns or 0).target,
            "timing_note": "Execution includes imports and fixtures; setup is unknown. Runtime fixture spans are nested, never additive wall time. Critical unit is last to finish, not a dependency-graph proof.",
            "python": python,
            "totals": totals,
            "serial": {
                module: SERIAL[module] for module in SERIAL if module in modules
            },
            "units": [
                {key: value for key, value in asdict(unit).items() if key != "output"}
                for unit in sorted(units, key=lambda unit: -unit.seconds)
            ],
        }
        arguments.json.write_text(json.dumps(summary, indent=2) + "\n")
    return 1 if any(unit.failed for unit in units) else 0


if __name__ == "__main__":
    raise SystemExit(main())
