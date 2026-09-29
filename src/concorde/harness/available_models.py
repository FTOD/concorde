"""Advisory model discovery, independent of Git and worker configuration.

These are configured candidates, not proof of API access. No inference request is made. Each
candidate names the project model names the model map already gives it as their local id, and a
complete listing names the map's ids the program does not list, to help fill the map.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .models import LEVELS, ModelConfigError, _program, load_model_map

# The command-line flag each backend takes the reasoning level with.
REASONING_FLAG = {"claude": "--effort", "pi": "--thinking"}
# Claude Code resolves these aliases for the account it is signed in to; it cannot list models.
CLAUDE_ALIASES = (
    (
        "fable",
        "the Fable model of the account's provider, for the hardest and longest work",
    ),
    ("opus", "the latest Opus model of the account's provider, for complex reasoning"),
    ("sonnet", "the latest Sonnet model of the account's provider, for daily coding"),
    ("haiku", "the fast Haiku model, for simple tasks"),
    ("opus[1m]", "Opus with a one million token context window"),
)
CLAUDE_PINNED = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
)
TIMEOUT = 60.0


def _run(argv: list[str], environ) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env=dict(environ),
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ModelConfigError(
            "discovery_failed",
            f"{' '.join(argv)} did not finish within {TIMEOUT:.0f}s",
        ) from error
    except OSError as error:
        raise ModelConfigError(
            "discovery_failed", f"{' '.join(argv)} could not start: {error}"
        ) from error


def _levels(backend: str, program: str, environ) -> list[str]:
    """The reasoning levels the program's --help lists, or the documented ones."""
    help_text = _run([program, "--help"], environ).stdout
    flag = re.escape(REASONING_FLAG[backend])
    found = re.search(
        flag + r"\s+<level>\s+.*?(?:\(|:\s*)([a-z]+(?:,\s*[a-z]+)+)",
        help_text,
        re.DOTALL,
    )
    if not found:
        return list(LEVELS[backend])
    return [item.strip() for item in found.group(1).split(",")]


def _version(program: str, environ) -> str:
    done = _run([program, "--version"], environ)
    lines = (done.stdout or done.stderr).strip().splitlines()
    return lines[-1].strip() if lines else ""


def _claude_settings(environ) -> tuple[Path, dict]:
    base = environ.get("CLAUDE_CONFIG_DIR")
    path = (
        Path(base) if base else Path(environ.get("HOME") or Path.home()) / ".claude"
    ) / ("settings.json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return path, {}
    return path, value if isinstance(value, dict) else {}


def _claude_models(levels: list[str], environ) -> tuple[list[dict], str]:
    path, settings = _claude_settings(environ)
    allowed = settings.get("availableModels")
    allowed = (
        [item for item in allowed if isinstance(item, str)]
        if isinstance(allowed, list)
        else None
    )
    models: list[dict] = []

    def add(model_id: str, source: str, note: str = "") -> None:
        if model_id and all(item["id"] != model_id for item in models):
            models.append(
                {
                    "id": model_id,
                    "source": source,
                    "reasoning": True,
                    "levels": list(levels),
                    "note": note,
                }
            )

    for alias, note in CLAUDE_ALIASES:
        if allowed is None or alias in allowed:
            add(alias, "Claude Code alias", note)
    for item in allowed or []:
        add(item, f"availableModels of {path}")
    if isinstance(settings.get("model"), str):
        add(
            settings["model"], f"model of {path}", "the main session's configured model"
        )
    for name in CLAUDE_PINNED:
        if environ.get(name):
            add(
                environ[name],
                f"environment variable {name}",
                "workers do not receive this variable, so the full name is passed",
            )
    note = (
        "Claude Code has no command that lists the models of the signed-in account, so this list "
        "holds its aliases and the models named in your settings and environment. A full model "
        "name such as claude-opus-5-5 can be configured directly. "
        "Credentials and account access are not verified; no API call is probed."
    )
    if allowed is not None:
        note += f" Only the aliases in availableModels of {path} are listed."
    return models, note


PI_ROW = re.compile(
    r"^(?P<provider>\S+)\s+(?P<model>\S+)\s+(?P<context>\S+)\s+(?P<max_out>\S+)\s+"
    r"(?P<thinking>yes|no)\s+(?P<images>yes|no)\s*$"
)


def _pi_models(program: str, levels: list[str], environ) -> tuple[list[dict], str]:
    quiet = dict(environ)
    quiet.update({"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"})
    argv = [program, "--no-extensions", "--list-models"]
    done = _run(argv, quiet)
    if done.returncode != 0:
        raise ModelConfigError(
            "discovery_failed",
            f"{' '.join(argv)} exited {done.returncode}: "
            + ((done.stderr or done.stdout).strip()[-2000:] or "(no output)"),
        )
    models = []
    for line in done.stdout.splitlines():
        row = PI_ROW.match(line.strip())
        if not row or row["provider"] == "provider":
            continue
        reasoning = row["thinking"] == "yes"
        models.append(
            {
                "id": f"{row['provider']}/{row['model']}",
                "source": "pi --list-models",
                "reasoning": reasoning,
                "levels": list(levels) if reasoning else ["off"],
                "context": row["context"],
                "max_output": row["max_out"],
                "images": row["images"] == "yes",
                "note": "",
            }
        )
    agent = environ.get("PI_CODING_AGENT_DIR") or "~/.pi/agent"
    note = (
        "pi lists the models it has credentials for in "
        f"{agent}; workers get a copy of its auth.json and models.json. "
        "These are configured credentialed candidates, not verified API access; no API call is probed."
    )
    if not models:
        note += (
            " It listed none: sign in with pi's /login or add a provider in models.json, then "
            f"list again. Its output was: {done.stdout.strip()[-500:] or '(empty)'}"
        )
    return models, note


def candidates(backend: str, environ=None) -> dict:
    """The models and reasoning levels the installed agent program offers workers."""
    if backend not in LEVELS:
        raise ModelConfigError(
            "discovery_failed", f"unknown backend {backend!r}; expected pi or claude"
        )
    environ = dict(os.environ if environ is None else environ)
    environ.update(
        {"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"}
    )
    program = _program(backend, environ)
    if not program:
        variable = "CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI"
        raise ModelConfigError(
            "backend_missing",
            f"the {backend} command is not installed: it is not on PATH and {variable} does not "
            "name an executable",
        )
    levels = _levels(backend, program, environ)
    if backend == "claude":
        models, note = _claude_models(levels, environ)
    else:
        models, note = _pi_models(program, levels, environ)
    mapping = _mapping(backend, models, environ)
    return {
        "backend": backend,
        "program": program,
        "version": _version(program, environ),
        "complete": backend == "pi",
        "reasoning_flag": REASONING_FLAG[backend],
        "reasoning_levels": levels,
        "models": models,
        "model_map": mapping,
        "note": note,
    }


def _mapping(backend: str, models: list[dict], environ) -> dict:
    """What the model map says of the listed models: each candidate's project model names, and,
    for a complete listing, the map's ids of this backend the program does not list. A missing
    or unreadable map is reported, never raised: discovery stays advisory."""
    try:
        path, mapped = load_model_map(environ)
    except ModelConfigError as error:
        for model in models:
            model["project_models"] = []
        return {
            "path": None,
            "error": {"code": error.code, "detail": str(error)},
            "unlisted": [],
        }
    ids = {model["id"] for model in models}
    for model in models:
        model["project_models"] = sorted(
            name for name, local in mapped.items() if local.get(backend) == model["id"]
        )
    return {
        "path": path.as_posix(),
        "error": None,
        "unlisted": sorted(
            (
                {"model": name, "id": local[backend]}
                for name, local in mapped.items()
                if backend in local and local[backend] not in ids
            ),
            key=lambda item: item["model"],
        )
        if backend == "pi"
        else [],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True, choices=("pi", "claude"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = candidates(args.backend)
    except ModelConfigError as error:
        if args.json:
            print(json.dumps({"error": {"code": error.code, "detail": str(error)}}))
        else:
            print(f"{error.code}: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        print(f"{value['backend']} candidates ({value['version']})")
        for model in value["models"]:
            names = ", ".join(model["project_models"]) or "none"
            print(
                f"  {model['id']}  reasoning: {', '.join(model['levels'])}  "
                f"project models: {names}"
            )
        mapping = value["model_map"]
        if mapping["error"]:
            print(
                f"model map: {mapping['error']['code']}: {mapping['error']['detail']}"
            )
        else:
            print(f"model map: {mapping['path']}")
            for item in mapping["unlisted"]:
                print(f"  {item['model']} maps to {item['id']}, which pi does not list")
        print(value["note"])
    return 0
