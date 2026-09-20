#!/usr/bin/env python3
"""Analyze local native Pi/session or pi-subagents event JSONL without emitting message bodies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from concorde.harness.timing import analyze_native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    records = []
    malformed = 0
    with args.input.open() as stream:
        for line in stream:
            try:
                records.append(json.loads(line))
            except ValueError:
                malformed += 1
    print(
        json.dumps(
            {**analyze_native(records), "malformed_records": malformed}, indent=2
        )
    )


if __name__ == "__main__":
    main()
