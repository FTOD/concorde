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
    envelope_file = scratch / "diagnostic-envelope.json"
    summary_file = scratch / "summary.json"
    summary = json.loads(summary_file.read_text()) if summary_file.exists() else {}
    if not envelope_file.exists():
        print(
            json.dumps(
                {
                    "diagnosticComplete": False,
                    "driverExit": executed.returncode,
                    "driverError": summary.get("driverError"),
                    "observationError": summary.get(
                        "observationError",
                        "no selected diagnostic envelope; no success claimed",
                    ),
                }
            )
        )
        return 3
    envelope = json.loads(envelope_file.read_text())
    envelope["summary"]["result"] = summary.get("result")
    envelope["summary"]["diagnosticComplete"] = summary.get("diagnosticComplete", False)
    if state.returncode == 0:
        facts = json.loads(state.stdout)
        envelope["summary"]["persistence"] = {
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
        envelope["summary"]["stateInspection"] = "failed"
    text = json.dumps(envelope, separators=(",", ":"))
    if len(text.encode()) >= 8000:
        raise ValueError(
            "final selected envelope exceeds 8000 bytes; no error detail dropped"
        )
    print(text)
    return 0 if envelope["summary"]["diagnosticComplete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
