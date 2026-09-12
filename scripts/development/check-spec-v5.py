#!/usr/bin/env python3
"""Offline audit of authored Protocol 5 Specs; does not admit a runtime repository.

Reuses only the unchanged Markdown grammar, diagram and offline schema helpers.
This is maintenance evidence, not a Framework lifecycle/readiness validator.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from concorde.spec.repository import (  # noqa: E402
    SpecDocument, _parse_definitions, _parse_entities, walk_lines,
)
from concorde.spec.schema import admit, validate  # noqa: E402
from concorde.spec.validation import architecture_findings, module_findings  # noqa: E402

ID = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
BLOCK = re.compile(r"^```(concorde-[\w-]+)\n(.*?)\n```\s*$", re.M | re.S)
LINK = re.compile(r"\[[^\]\n]+\]\(([^\s)]+)\)")


def decode(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError(f"duplicate JSON key: {key}")
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def blocks(text, kind):
    return [decode(m[2]) for m in BLOCK.finditer(text) if m[1] == kind]


def digest(raw):
    return "sha256:" + sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path, directory=False):
    value = path[:-1] if directory and path.endswith("/") else path
    parts = value.split("/")
    require(value and not value.startswith("/") and "\\" not in value
            and all(p not in {"", ".", ".."} for p in parts), f"unsafe path: {path}")
    current = ROOT
    for part in parts:
        current /= part
        require(not current.is_symlink(), f"symlink: {path}")
    return current


def resolve(targets, docs, module_id):
    """One-level inclusion with all reasons; deliberately never calls itself."""
    target = targets[module_id]
    reasons = defaultdict(set)
    by_id = {d.document_id: path for path, d in docs.items()}
    for path in target["documents"]:
        reasons[path].add(("owned", module_id))
    refs = target["references"]
    require(len({(r["kind"], r["id"]) for r in refs}) == len(refs), "duplicate reference")
    for ref in refs:
        require(set(ref) == {"kind", "id"}, "reference fields")
        kind, identity = ref["kind"], ref["id"]
        if kind == "module":
            require(identity in targets and identity != module_id, f"invalid Module reference: {ref}")
            paths = targets[identity]["documents"]
        else:
            require(kind == "document" and identity in by_id, f"invalid document reference: {ref}")
            paths = [by_id[identity]]
            require(paths[0] not in target["documents"], "reference to owned document")
        for path in paths:
            reasons[path].add((kind, identity))
    return {p: sorted(reasons[p]) for p in sorted(reasons)}


def resolution_examples():
    """Exercise overlap, cycles, narrow references, drift and rejected declarations."""
    docs = {p: SimpleNamespace(document_id=i) for p, i in
            [("a/module.md", "document.a"), ("b/module.md", "document.b"),
             ("b/interface.md", "document.interface"), ("c/module.md", "document.c")]}
    targets = {
        "module.a": {"documents": ["a/module.md"], "references": [
            {"kind": "module", "id": "module.b"},
            {"kind": "document", "id": "document.interface"}]},
        "module.b": {"documents": ["b/module.md", "b/interface.md"],
                     "references": [{"kind": "module", "id": "module.c"}]},
        "module.c": {"documents": ["c/module.md"],
                     "references": [{"kind": "module", "id": "module.a"}]},
    }
    overlap = resolve(targets, docs, "module.a")
    require(list(overlap) == ["a/module.md", "b/interface.md", "b/module.md"], "recursive expansion in overlap fixture")
    require(overlap["b/interface.md"] == [("document", "document.interface"), ("module", "module.b")], "lost inclusion reason")
    require(list(resolve(targets, docs, "module.b")) == ["b/interface.md", "b/module.md", "c/module.md"], "provider selection must resolve its own references")
    targets["module.a"]["references"].pop()
    reduced = resolve(targets, docs, "module.a")
    require(overlap.keys() == reduced.keys() and overlap != reduced, "reference-only provenance drift")
    targets["module.a"]["references"] = [{"kind": "document", "id": "document.interface"}]
    require(list(resolve(targets, docs, "module.a")) == ["a/module.md", "b/interface.md"], "document reference must not include provider siblings")
    bad = [
        [{"kind": "module", "id": "module.a"}],
        [{"kind": "document", "id": "document.a"}],
        [{"kind": "module", "id": "document.interface"}],
        [{"kind": "document", "id": "document.missing"}],
        [{"kind": "document", "id": "document.interface"}] * 2,
    ]
    for refs in bad:
        targets["module.a"]["references"] = refs
        try:
            resolve(targets, docs, "module.a")
        except ValueError:
            continue
        raise ValueError(f"invalid references admitted: {refs}")
    return 9


def audit(base=None):
    example_count = resolution_examples()
    registry = decode((ROOT / ".concorde/specs.json").read_text())
    config = decode((ROOT / ".concorde/config.json").read_text())
    require(registry["schema_version"] == 4 and config["profile_version"] == 12, "version binding")
    require(set(registry) == {"schema_version", "project_id", "entry_target", "targets", "checks"}, "registry fields")
    targets = {t["id"]: t for t in registry["targets"]}
    require(len(targets) == len(registry["targets"]) and registry["entry_target"] in targets, "Module identity")
    docs, identities, entities, requirements, scenarios, contracts, bindings = {}, {}, {}, {}, {}, {}, []
    physical_files = set()
    def identity(value, path, owner):
        require(ID.fullmatch(value) and value not in identities, f"duplicate/invalid ID: {value}")
        identities[value] = (path, owner)
    for key, target in targets.items():
        identity(key, None, key)
        require(set(target) == {"id", "kind", "title", "documents", "references", "parent", "uses", "files", "checks"}, f"Module fields: {key}")
        require(target["kind"] == "module" and target["title"].strip(), f"Module kind/title: {key}")
        require(isinstance(target["references"], list), f"reference array: {key}")
        require(target["documents"] and len([p for p in target["documents"] if PurePosixPath(p).name == "module.md"]) == 1, f"reading entry: {key}")
        for field in ("documents", "uses", "files", "checks"):
            require(len(set(target[field])) == len(target[field]), f"duplicate {field}: {key}")
        require(set(target["uses"]) <= targets.keys() and key not in target["uses"], f"uses: {key}")
        seen, parent = {key}, target["parent"]
        while parent is not None:
            require(parent in targets and parent not in seen, f"composition: {key}")
            seen.add(parent)
            parent = targets[parent]["parent"]
        entities[key] = []
        for path in target["documents"]:
            require(path not in docs and path.endswith(".md"), f"multiple ownership/path: {path}")
            raw = safe(path).read_bytes()
            stat = safe(path).stat()
            physical = (stat.st_dev, stat.st_ino)
            require(physical not in physical_files, f"physical document alias: {path}")
            physical_files.add(physical)
            text = raw.decode("utf-8")
            require(text.strip() and not re.search(r"[\u3400-\u9fff]", text), f"empty/non-English document: {path}")
            metadata = blocks(text, "concorde-document")
            require(len(metadata) == 1, f"document metadata count: {path}")
            meta = metadata[0]
            require(set(meta) == {"id", "owner", "main_visible"} and meta["owner"] == key
                    and type(meta["main_visible"]) is bool, f"owner metadata: {path}")
            identity(meta["id"], path, key)
            # The legacy record is only a carrier for unchanged syntax parsers; no loader is used.
            doc = SpecDocument(path, text, digest(raw), meta["id"], (key,), meta["main_visible"], meta, text)
            docs[path] = doc
            sc, req = _parse_definitions(doc, key)
            es = _parse_entities(doc, key)
            for item in sc + req + es:
                identity(item.id, path, key)
            scenarios.update({s.id: s for s in sc})
            requirements.update({r.id: r for r in req})
            entities[key].extend(es)
            for contract in blocks(text, "concorde-contract"):
                require(set(contract) == {"id", "version", "schema", "semantics", "example"}, f"canonical contract fields: {path}")
                require(type(contract["version"]) is int and contract["version"] > 0 and contract["semantics"].strip(), "contract metadata")
                identity(contract["id"], path, key)
                admit(contract["schema"])
                validate(contract["example"], contract["schema"])
                contracts[contract["id"]] = (contract, path, key)
            bindings.extend((b, path, key) for b in blocks(text, "concorde-contract-binding"))
    require(set(docs) == {str(p.relative_to(ROOT)) for p in (ROOT / "specs").rglob("*.md")}, "unregistered Spec document")
    contexts = {key: resolve(targets, docs, key) for key in targets}
    facade = SimpleNamespace(targets={key: SimpleNamespace(id=key, primary_document=next(p for p in t["documents"] if PurePosixPath(p).name == "module.md")) for key, t in targets.items()}, document=docs.__getitem__)
    findings = list(module_findings(facade))
    for key, target in targets.items():
        local = entities[key]
        findings.extend(architecture_findings(facade, facade.targets[key], local))
        require(len({e.title for e in local}) == len(local), f"entity titles: {key}")
        entries = [entry for e in local for entry in e.files]
        require(len(set(entries)) == len(entries) and set(entries) == set(target["files"]), f"entity/file union: {key}")
        for e in local:
            for entry in e.files:
                path = safe(entry, True)
                require(entry in e.pending or (path.is_dir() if entry.endswith("/") else path.is_file()), f"missing unmarked file: {entry}")
                require(not entry.startswith(("generated/", ".concorde/", ".agents/", ".claude/")), f"forbidden file binding: {entry}")
                require(not any(p == entry or entry.endswith("/") and p.startswith(entry) for p in docs), f"Spec bound as code: {entry}")
        providers = set(target["uses"]) | {k for k, t in targets.items() if t["parent"] == key}
        require(Counter(e.target_id for e in local if e.target_id) == Counter({p: 1 for p in providers}), f"collaborator entities: {key}")
        deps = [d for path in target["documents"] for block in blocks(docs[path].content, "concorde-dependencies") for d in block]
        require(Counter(d["target_id"] for d in deps) == Counter({p: 1 for p in providers}), f"dependency coverage: {key}")
        for dep in deps:
            require(set(dep) == {"target_id", "responsibility", "selection_condition", "relied_upon_promises"}, "dependency fields")
            require(dep["responsibility"].strip() and dep["selection_condition"].strip() and dep["relied_upon_promises"], "dependency meaning")
    require(not findings, "\n".join(str(f) for f in findings))
    for binding, path, key in bindings:
        require(set(binding) == {"id", "version", "role", "peer", "selection_condition", "relied_upon_guarantees", "obligations"}, f"binding fields: {path}")
        contract, definition, _ = contracts[binding["id"]]
        require(type(binding["version"]) is int and binding["version"] == contract["version"] and definition in contexts[key], f"binding definition/version/context: {path}")
        require(binding["role"] in {"provided", "required"} and binding["selection_condition"].strip(), "binding role/condition")
        for field in ("relied_upon_guarantees", "obligations"):
            require(binding[field] and len(set(binding[field])) == len(binding[field]) and all(isinstance(x, str) and x.strip() for x in binding[field]), f"binding {field}")
        peer = binding["peer"]
        require(peer in targets or re.fullmatch(r"external:[a-z][a-z0-9-]*", peer), "binding peer")
        if peer in targets:
            require(any(owner == peer and b["peer"] == key and b["id"] == binding["id"] and b["version"] == binding["version"] and b["role"] != binding["role"] for b, _, owner in bindings), f"unmatched internal binding: {path}")
    keys = [(key, b["id"], b["role"], b["peer"]) for b, _, key in bindings]
    require(len(set(keys)) == len(keys), "duplicate participant binding")
    # Links in prose and structured semantic strings are navigation; only required local
    # dependency/binding links must be included in their participant's context.
    link_count = 0
    for path, doc in docs.items():
        prose = "\n".join(line for _, kind, line in walk_lines(doc.content) if kind == "prose")
        semantic = []
        for kind in ("concorde-dependencies", "concorde-contract-binding"):
            for value in blocks(doc.content, kind):
                semantic.append(json.dumps(value))
        for required, text in ((False, prose), (True, "\n".join(semantic))):
            for href in LINK.findall(text):
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                location = (ROOT / path).parent / unquote(url.path) if url.path else ROOT / path
                destination = str(location.resolve().relative_to(ROOT))
                require(location.exists(), f"missing link: {path} -> {href}")
                fragment = unquote(url.fragment)
                if fragment.startswith(("req.", "scenario.", "entity.", "contract.")):
                    require(fragment in identities and identities[fragment][0] == destination, f"wrong ID anchor: {path} -> {href}")
                elif fragment and destination in docs:
                    headings = [line.lstrip('#').strip() for _, kind, line in walk_lines(docs[destination].content) if kind == 'prose' and line.startswith('#')]
                    slugs = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                    require(fragment in slugs, f"missing heading anchor: {path} -> {href}")
                if required:
                    require(destination in contexts[doc.metadata["owner"]], f"required definition outside context: {path} -> {href}")
                link_count += 1
    stable = 0
    if base:
        old_registry = decode(subprocess.check_output(["git", "show", f"{base}:.concorde/specs.json"], cwd=ROOT, text=True))
        for target in old_registry["targets"]:
            for path in target["documents"]:
                text = subprocess.check_output(["git", "show", f"{base}:{path}"], cwd=ROOT, text=True)
                ids = re.findall(r"^#{2,5} ((?:req|scenario)\.[\w.-]+)\s+[—–-]", text, re.M)
                ids += [e["id"] for block in blocks(text, "concorde-entities") for e in block]
                for value in ids:
                    require(value in identities and identities[value][1] == target["id"], f"lost/transferred stable ID: {value}")
                    stable += 1
    manifest = decode((ROOT / "protocol/manifest.json").read_text())
    require(manifest["version"] == "5.0.0" and manifest["source_profile"] == 12, "manifest version")
    require(config["protocol"] == {"version": "5.0.0", "digest": digest((ROOT / "protocol/manifest.json").read_bytes())}, "manifest binding")
    for asset in manifest["assets"]:
        require(asset["digest"] == digest(safe(asset["path"]).read_bytes()), f"asset digest: {asset['path']}")
    return {"status": "passed", "modules": len(targets), "documents": len(docs),
            "requirements": len(requirements), "scenarios": len(scenarios), "entities": sum(map(len, entities.values())),
            "canonical_contracts": len(contracts), "bindings": len(bindings), "links": link_count,
            "reference_boundary_cases": example_count,
            "preserved_baseline_ids": stable, "context_files": {k: len(v) for k, v in contexts.items()},
            "semantic_completeness": "not_proven", "runtime_support": "not_implemented"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git revision whose stable definition IDs must be preserved")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.base), indent=2))
    except (ValueError, KeyError, OSError) as error:
        print(f"Spec v5 audit failed: {error}", file=sys.stderr)
        sys.exit(1)
