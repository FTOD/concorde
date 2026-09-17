#!/usr/bin/env python3
"""Offline Protocol-9 source audit; historical command path retained for configured checks.

Checks complete document units without launching a worker. --base additionally checks stable
requirement/scenario/entity identities against a committed baseline, including Protocol-6 sources.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from concorde.spec.content_repository import DocumentUnitRepository
from concorde.spec.content_model import reading_meanings
from concorde.spec.repository_base import digest, read_file, walk_lines
from concorde.spec.typed_data import decode


def json_value(raw: str | bytes):
    return decode(raw.decode("utf-8") if isinstance(raw, bytes) else raw)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(base=None):
    repository = DocumentUnitRepository(ROOT)
    repository.validate()
    identities = {}
    requirements, scenarios, entities, contracts, bindings = [], [], [], [], []
    for target in repository.targets.values():
        local = repository.definitions(target)
        requirements.extend(local.requirements)
        scenarios.extend(local.scenarios)
        entities.extend(local.entities)
        contracts.extend(repository.contracts(target))
        bindings.extend(repository.contract_bindings(target))
        for item in (*local.requirements, *local.scenarios, *local.entities):
            identities[item.id] = (item.document, item.owner)
        for contract in repository.contracts(target):
            identities[contract["id"]] = (contract["source"], contract["owner"])
    registered = set(repository.source_documents)
    physical = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "specs").rglob("*")
        if p.is_file() and (p.suffix == ".md" or p.name.endswith(".md.json"))
    }
    require(physical == registered, "unregistered or missing document-unit member")
    anchors = {}
    for path in repository.document_targets:
        text = repository.document(path).body
        require(
            not re.search(r"[\u3400-\u9fff]", text),
            f"non-English reading content: {path}",
        )
        titles = [
            line.lstrip("#").strip()
            for _, kind, line in walk_lines(text)
            if kind == "prose" and line.startswith("#")
        ]
        anchors[path] = {
            re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in titles
        }
        anchors[path].update(meaning.anchor for meaning in reading_meanings(text, path))
    for identity, (path, _) in identities.items():
        anchors[path].add(identity)
    links = 0
    for path in repository.document_targets:
        text = "\n".join(
            line
            for _, kind, line in walk_lines(repository.document(path).body)
            if kind == "prose"
        )
        for href in re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", text):
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            destination = (
                ((ROOT / path).parent / unquote(url.path)).resolve()
                if url.path
                else ROOT / path
            )
            relative = destination.relative_to(ROOT).as_posix()
            require(destination.exists(), f"missing link: {path} -> {href}")
            if url.fragment and relative in anchors:
                require(
                    unquote(url.fragment) in anchors[relative],
                    f"missing anchor: {path} -> {href}",
                )
            links += 1
    preserved = 0
    if base:
        old = json_value(
            subprocess.check_output(
                ["git", "show", f"{base}:.concorde/specs.json"], cwd=ROOT
            )
        )
        for target in old["targets"]:
            require(
                target["id"] in repository.targets,
                f"lost Module identity: {target['id']}",
            )
            for path in target["documents"]:
                text = subprocess.check_output(
                    ["git", "show", f"{base}:{path}"], cwd=ROOT, text=True
                )
                if old["schema_version"] == 4:
                    header = re.search(
                        r"^```concorde-document\s*\n(.*?)^```", text, re.M | re.S
                    )
                    if header is None:
                        raise ValueError(f"missing baseline document identity: {path}")
                    previous_id = json_value(header.group(1))["id"]
                else:
                    previous_id = json_value(
                        subprocess.check_output(
                            ["git", "show", f"{base}:{path}.json"], cwd=ROOT
                        )
                    )["document"]["id"]
                current_path = repository._document_index().get(previous_id)
                if current_path is None:
                    raise ValueError(f"lost document identity: {previous_id}")
                current = repository.unit(current_path)
                require(
                    current.owner == target["id"],
                    f"transferred document identity: {path}",
                )
                preserved += 1
                ids = re.findall(
                    r"^#{2,5} ((?:req|scenario)\.[\w.-]+)\s+[—–-]", text, re.M
                )
                if old["schema_version"] == 4:
                    for raw in re.findall(
                        r"^```concorde-entities\s*\n(.*?)^```", text, re.M | re.S
                    ):
                        ids.extend(e["id"] for e in json_value(raw))
                else:
                    meta = json_value(
                        subprocess.check_output(
                            ["git", "show", f"{base}:{path}.json"], cwd=ROOT
                        )
                    )
                    ids.extend(e["id"] for e in meta["entities"])
                for raw in re.findall(
                    r"^```concorde-contract\s*\n(.*?)^```", text, re.M | re.S
                ):
                    ids.append(json_value(raw)["id"])
                for identity in ids:
                    require(
                        identity in identities
                        and identities[identity][1] == target["id"],
                        f"lost/transferred stable ID: {identity}",
                    )
                    preserved += 1
    manifest = json_value(read_file(ROOT, "protocol/manifest.json"))
    config = json_value(read_file(ROOT, ".concorde/config.json"))
    require(
        manifest["version"] == "9.0.0" and manifest["source_profile"] == 14,
        "manifest version",
    )
    require(
        config["profile_version"] == 14
        and config["protocol"]
        == {
            "version": "9.0.0",
            "digest": digest(read_file(ROOT, "protocol/manifest.json")),
        },
        "Protocol binding",
    )
    for asset in manifest["assets"]:
        require(
            asset["digest"] == digest(read_file(ROOT, asset["path"])),
            f"stale Protocol asset: {asset['path']}",
        )
    return {
        "status": "passed",
        "modules": len(repository.targets),
        "documents": len(repository.document_targets),
        "source_members": len(registered),
        "requirements": len(requirements),
        "scenarios": len(scenarios),
        "entities": len(entities),
        "canonical_contracts": len(contracts),
        "bindings": len(bindings),
        "links": links,
        "preserved_baseline_ids": preserved,
        "context_files": {
            t.id: len(repository.spec_files(t.id)) for t in repository.targets.values()
        },
        "semantic_completeness": "not_proven",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base", help="Committed revision whose definition identities must survive"
    )
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.base), indent=2))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Spec v9 audit failed: {error}", file=sys.stderr)
        raise SystemExit(1)
