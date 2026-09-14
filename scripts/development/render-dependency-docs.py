#!/usr/bin/env python3
"""Render the vendored reference documentation of an installed Python dependency.

Concorde's Modules declare the documentation of the external capabilities they use as entity
``documentation`` entries (Spec Protocol 5.1). This script produces that material for a Python
package from the installed distribution itself, so the vendored reference is pinned to the exact
version the project runs and needs no network: one Markdown file per public module with every
public name's signature and docstring, plus an index recording the version and the command.

    python3 scripts/development/render-dependency-docs.py langgraph docs/vendor/langgraph \\
        langgraph.graph langgraph.graph.state langgraph.types langgraph.runtime ...

Rerun it after upgrading the dependency; the Spec entity binds the directory, so the Module's
capability context follows the regenerated files.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import shutil
import sys
from pathlib import Path


def _signature(value) -> str:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return ""


def _public_names(module) -> list[str]:
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in dir(module) if not name.startswith("_")]
    return sorted(name for name in names if hasattr(module, name))


def _render_member(name: str, value, level: int) -> list[str]:
    heading = "#" * level
    lines: list[str] = []
    if inspect.isclass(value):
        bases = ", ".join(base.__name__ for base in value.__bases__ if base is not object)
        lines.append(f"{heading} class `{name}{_signature(value)}`" + (f" (bases: {bases})" if bases else ""))
        doc = inspect.getdoc(value)
        if doc:
            lines.extend(["", doc])
        for member_name, member in sorted(vars(value).items()):
            if member_name.startswith("_") and member_name != "__init__":
                continue
            unwrapped = member.__func__ if isinstance(member, (classmethod, staticmethod)) else member
            if callable(unwrapped) and not inspect.isclass(unwrapped):
                lines.append("")
                lines.append(f"{heading}# `{name}.{member_name}{_signature(unwrapped)}`")
                member_doc = inspect.getdoc(unwrapped)
                if member_doc:
                    lines.extend(["", member_doc])
            elif isinstance(member, property):
                lines.append("")
                lines.append(f"{heading}# property `{name}.{member_name}`")
                member_doc = inspect.getdoc(member)
                if member_doc:
                    lines.extend(["", member_doc])
    elif callable(value):
        lines.append(f"{heading} `{name}{_signature(value)}`")
        doc = inspect.getdoc(value)
        if doc:
            lines.extend(["", doc])
    else:
        lines.append(f"{heading} `{name}`")
        lines.append("")
        lines.append(f"Value of type `{type(value).__name__}`: `{value!r}`"[:400])
    return lines


def render_module(module_name: str) -> str:
    module = importlib.import_module(module_name)
    lines = [f"# `{module_name}`", ""]
    doc = inspect.getdoc(module)
    if doc:
        lines.extend([doc, ""])
    names = _public_names(module)
    lines.append("Public names: " + ", ".join(f"`{name}`" for name in names))
    for name in names:
        value = getattr(module, name)
        if inspect.ismodule(value):
            continue
        lines.append("")
        lines.extend(_render_member(name, value, 2))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("distribution", help="installed distribution name, e.g. langgraph")
    parser.add_argument("output", help="project-relative output directory")
    parser.add_argument("modules", nargs="+", help="importable public modules to document")
    arguments = parser.parse_args(argv)
    version = importlib.metadata.version(arguments.distribution)
    output = Path(arguments.output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    rendered = []
    for module_name in arguments.modules:
        text = render_module(module_name)
        path = output / (module_name.replace(".", "_") + ".md")
        path.write_text(text, encoding="utf-8")
        rendered.append((module_name, path.name, len(text.encode("utf-8"))))
    index = [f"# {arguments.distribution} {version} API reference", "",
             f"Vendored reference documentation of `{arguments.distribution}` version `{version}`, rendered from "
             "the installed distribution's public modules (signatures and docstrings) by "
             "`scripts/development/render-dependency-docs.py`. It is the admitted source of this "
             "dependency's API facts for Concorde's planning, task-authoring, implementation and "
             "code-review phases. Regenerate it after upgrading the dependency:", "",
             "```sh", "python3 scripts/development/render-dependency-docs.py " + arguments.distribution + " "
             + arguments.output + " \\", "    " + " ".join(arguments.modules), "```", "",
             "| Module | File | Bytes |", "| --- | --- | --- |"]
    index.extend(f"| `{module_name}` | [{name}]({name}) | {size} |" for module_name, name, size in rendered)
    (output / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"rendered {len(rendered)} modules of {arguments.distribution} {version} into {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
