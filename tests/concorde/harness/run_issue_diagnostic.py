"""One source-owned Issue diagnostic command. --selftest never opens auth or calls a model."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(SOURCE / "src"), str(SOURCE)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selftest", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--auth-source", type=Path)
    parser.add_argument("--models-source", type=Path)
    args = parser.parse_args()
    from concorde.distribution.session_selection import load_selection
    from concorde.harness.native_runtime import admit_native_runtime

    selected = load_selection(SOURCE, args.selection)
    if selected["mode"] != "test" or os.environ.get(
        "CONCORDE_SESSION_SELECTION"
    ) != str(args.selection):
        raise ValueError("exact governing source test selection must remain active")
    admit_native_runtime(args.native)
    if args.live and not all((args.model, args.auth_source, args.models_source)):
        raise ValueError(
            "live execution needs explicit model and separately approved auth/model-file paths"
        )
    scratch = Path(os.environ["CONCORDE_CHECK_TMPDIR"]) / "issue-diagnostic"
    scratch.mkdir(
        mode=0o700
    )  # Fresh command/ticket; never replay a previous directory.
    environment = {
        **os.environ,
        "C": str(SOURCE),
        "S": str(scratch),
        "SDK": str(args.sdk),
        "NATIVE": str(args.native),
        "PYTHONPATH": str(SOURCE / "src") + os.pathsep + str(SOURCE),
        "CONCORDE_DIAGNOSTIC_MODEL": args.model or "fixture/model",
    }
    # This host drives explicit native calls; it is not a task-child delegation request.
    environment.pop("PI_SUBAGENT_CHILD", None)
    if args.live:
        environment.update(
            CONCORDE_DIAGNOSTIC_AUTH=str(args.auth_source),
            CONCORDE_DIAGNOSTIC_MODELS=str(args.models_source),
        )
    driver = SOURCE / "tests/concorde/harness/issue_live_diagnostic.mjs"
    subprocess.run(
        ["node", "--check", str(driver)],
        env=environment,
        check=True,
        capture_output=True,
    )
    bootstrap = subprocess.run(
        ["node", str(driver), "--selftest"],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(bootstrap.stdout)["realModelCalls"] == 0
    subprocess.run(
        [
            sys.executable,
            str(SOURCE / "tests/concorde/harness/issue_diagnostic_setup.py"),
        ],
        cwd=SOURCE,
        env=environment,
        check=True,
        capture_output=True,
    )
    if not args.live:
        print(
            json.dumps(
                {
                    "selftest": True,
                    "fixtureValidated": True,
                    "codecRoundtrip": True,
                    "realModelCalls": 0,
                }
            )
        )
        return 0
    executed = subprocess.run(
        ["node", str(driver), "--live"],
        cwd=SOURCE,
        env=environment,
        capture_output=True,
        text=True,
        timeout=1150,
        check=False,
    )
    # Never emit arbitrary driver stdout/stderr, transcripts, auth or file read results.
    state = subprocess.run(
        [
            sys.executable,
            str(SOURCE / "tests/concorde/harness/issue_diagnostic_state.py"),
        ],
        cwd=SOURCE,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    summary_file = scratch / "summary.json"
    summary = json.loads(summary_file.read_text()) if summary_file.exists() else {}
    if not summary.get("report"):
        summary["diagnosticComplete"] = False
        summary.setdefault(
            "observationError", "no selected diagnostic report; no success claimed"
        )
    # The selected diagnostic is an explicit test_command report, not an 8KB stdout payload.
    # Request reports=["structured-tool.json", "diagnostic-summary.json"] on that command.
    summary["driverExit"] = executed.returncode
    if state.returncode == 0:
        facts = json.loads(state.stdout)
        summary["persistence"] = {
            key: facts.get(key)
            for key in (
                "issueStatus",
                "disposition",
                "reportsImmutable",
                "specCodeConfigUnchanged",
                "status",
                "phase",
                "attempts",
                "acceptedDecisions",
                "verificationDigests",
                "pendingJournal",
                "validatedTree",
                "delivered",
            )
        }
    else:
        summary["stateInspection"] = "failed"
    report = Path(os.environ["CONCORDE_CHECK_REPORT_DIR"]) / "diagnostic-summary.json"
    with report.open("x") as stream:
        os.chmod(report, 0o600)
        stream.write(json.dumps(summary))
    print(
        json.dumps(
            {
                "diagnosticComplete": summary["diagnosticComplete"],
                "report": summary.get("report"),
                "driverExit": executed.returncode,
            }
        )
    )
    return 0 if summary["diagnosticComplete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
