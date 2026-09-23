"""Checked project-discovery projections for Task subagents, never Operation workers."""

import json
from pathlib import Path

from .prompt_resolver import resolve_role_prompt
from agents.task_subagent import TASK_SUBAGENT_PROFILES

TESTER = next(p.prompt for p in TASK_SUBAGENT_PROFILES if p.name == "tester")
COORDINATOR = "prompts/user-session/source/coordinator.md"
BRIEF_LIFECYCLE = "pi/extensions/concorde-brief-lifecycle.ts"


def prompt_roots(root: Path) -> tuple[str, ...]:
    return tuple(
        p
        for p in (*[profile.prompt for profile in TASK_SUBAGENT_PROFILES], COORDINATOR)
        if (root / p).is_file()
    )


def render(root: Path, framework_prefix: str = ""):
    from .build import BuildError, BuildOutput

    if not (root / TESTER).is_file():
        if (root / "concorde.json").exists() or (
            root / "prompts/task-subagent"
        ).exists():
            raise BuildError("canonical tester prompt is missing")
        return ()  # Prompt-only historical deterministic fixtures without Task subagent assets.
    prefix = framework_prefix.strip("/")
    if (root / "concorde.json").is_file():
        assets = ["concorde-observe.ts", "concorde-selection.ts", "concorde-tester.ts"]
        if not prefix:
            assets.extend(("concorde-maintenance.ts", "concorde-brief-lifecycle.ts"))
        for asset in assets:
            path = root / "pi/extensions" / asset
            if not path.is_file() or path.is_symlink():
                raise BuildError(
                    f"Task subagent runtime asset is missing or unsafe: {asset}"
                )
    assets = f"../../{prefix + '/' if prefix else ''}pi/extensions"
    entry = (
        "../extensions/concorde-session.ts"
        if prefix
        else "../../generated/session/pi/concorde-session.ts"
    )
    outputs = []
    for profile in sorted(TASK_SUBAGENT_PROFILES, key=lambda p: p.name, reverse=True):
        if prefix and profile.source_only:
            continue
        name, source = profile.name, profile.prompt
        tools = ", ".join(profile.tools)
        extensions = ", ".join(f"{assets}/{ext}" for ext in profile.extensions)
        if name == "tester":
            extensions += f", {entry}"
        resolved = resolve_role_prompt(root, source)
        body = (
            f"---\nname: {name}\ndescription: Concorde {name} Task subagent\n"
            f"tools: {tools}\nextensions: {extensions}\n"
            + (
                f"acceptanceRole: {profile.acceptance_role}\n"
                if profile.acceptance_role
                else ""
            )
            + "systemPromptMode: replace\ninheritProjectContext: false\n"
            "inheritGlobalContext: false\ninheritSkills: false\ndefaultContext: fresh\n"
            "excludeTools: subagent\nasync: true\ncompletionGuard: false\n---\n"
            "<!-- Generated from canonical prompts/task-subagent sources; do not edit. -->\n\n"
            + resolved.body
        )
        outputs.append(
            BuildOutput(f".pi/agents/{name}.md", body.encode(), resolved.sources)
        )
    if not prefix:
        resolved = resolve_role_prompt(root, COORDINATOR)
        outputs.append(
            BuildOutput(
                ".pi/extensions/concorde-coordinator.ts",
                (
                    "// Generated source user session extension; excluded from child extension lists.\n"
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
    if not prefix:
        outputs.append(
            BuildOutput(
                ".pi/extensions/concorde-brief-lifecycle.ts",
                (
                    "// Generated explicit source user session lifecycle entry; no Operation catalog.\n"
                    f'export {{ userSessionLifecycle as default }} from "{assets}/concorde-brief-lifecycle.ts";\n'
                ).encode(),
                ((BRIEF_LIFECYCLE,) if (root / BRIEF_LIFECYCLE).is_file() else ()),
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
