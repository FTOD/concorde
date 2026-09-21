"""Checked project-discovery projections for outer task roles, never Operation workers."""

import json
from pathlib import Path

from .prompt_resolver import resolve_role_prompt

TESTER = "prompts/outer/tester.md"
SOURCE_ROOTS = (
    "prompts/outer/source/main.md",
    "prompts/outer/source/maintenance-worker.md",
)


def prompt_roots(root: Path) -> tuple[str, ...]:
    return tuple(p for p in (TESTER, *SOURCE_ROOTS) if (root / p).is_file())


def render(root: Path, framework_prefix: str = ""):
    from .build import BuildError, BuildOutput

    if not (root / TESTER).is_file():
        if (root / "concorde.json").exists() or (root / "prompts/outer").exists():
            raise BuildError("canonical tester prompt is missing")
        return ()  # Prompt-only historical deterministic fixtures without outer assets.
    prefix = framework_prefix.strip("/")
    if (root / "concorde.json").is_file():
        assets = ["concorde-observe.ts", "concorde-selection.ts", "concorde-tester.ts"]
        if not prefix:
            assets.append("concorde-maintenance.ts")
        for asset in assets:
            path = root / "pi/extensions" / asset
            if not path.is_file() or path.is_symlink():
                raise BuildError(
                    f"outer role runtime asset is missing or unsafe: {asset}"
                )
    assets = f"../../{prefix + '/' if prefix else ''}pi/extensions"
    entry = (
        "../extensions/concorde-session.ts"
        if prefix
        else "../../generated/session/pi/concorde-session.ts"
    )
    roles = [
        (
            "tester",
            TESTER,
            "read, grep, find, ls, test_command",
            f"{assets}/concorde-tester.ts, {entry}",
        )
    ]
    if not prefix:
        roles.append(
            (
                "maintenance-worker",
                SOURCE_ROOTS[1],
                "read, grep, find, ls, bash, edit, write",
                f"{assets}/concorde-maintenance.ts",
            )
        )
    outputs = []
    for name, source, tools, extensions in roles:
        resolved = resolve_role_prompt(root, source)
        body = (
            f"---\nname: {name}\ndescription: Concorde {name} sibling task role\n"
            f"tools: {tools}\nextensions: {extensions}\n"
            + ("acceptanceRole: read-only\n" if name == "tester" else "")
            + "systemPromptMode: replace\ninheritProjectContext: false\n"
            "inheritGlobalContext: false\ninheritSkills: false\ndefaultContext: fresh\n"
            "excludeTools: subagent\nasync: true\ncompletionGuard: false\n---\n"
            "<!-- Generated from canonical prompts/outer sources; do not edit. -->\n\n"
            + resolved.body
        )
        outputs.append(
            BuildOutput(f".pi/agents/{name}.md", body.encode(), resolved.sources)
        )
    if not prefix:
        resolved = resolve_role_prompt(root, SOURCE_ROOTS[0])
        outputs.append(
            BuildOutput(
                ".pi/extensions/concorde-coordinator.ts",
                (
                    "// Generated source-main extension; excluded from child extension lists.\n"
                    "// No Operation catalog, tools, or session control.\n"
                    'import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";\n'
                    "const COORDINATOR = " + json.dumps(resolved.body) + ";\n"
                    "export default function (pi: ExtensionAPI) {\n"
                    '\tpi.on("before_agent_start", (event) => ({\n'
                    '\t\tsystemPrompt: event.systemPrompt.trimEnd() + "\\n\\n" + COORDINATOR,\n'
                    "\t}));\n"
                    "}\n"
                ).encode(),
                resolved.sources,
            )
        )
    outputs.append(
        BuildOutput(
            ".pi/extensions/concorde-observe.ts",
            (
                "// Generated passive observer; no Operation catalog.\n"
                f'export {{ default }} from "{assets}/concorde-observe.ts";\n'
            ).encode(),
            (),
        )
    )
    return tuple(outputs)
