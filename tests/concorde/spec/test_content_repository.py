"""Staged new-format contexts through real source delivery, review and transaction helpers."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.context import (
    _stale_on_resolution_error,
    context_documents,
    context_grants,
    materialize_documents,
)
from concorde.harness.effects import EffectDeclaration
from concorde.harness.permissions import PolicyBinding, compile_policy
from concorde.review.review import _changes
from concorde.spec.content_changes import (
    apply_author_changes,
    author_candidate,
    confirm_pending_units,
    pending_changes,
)
from concorde.spec.content_model import metadata_path
from concorde.spec.content_repository import (
    DocumentUnitRepository,
    unit_resolution_schema,
)
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.typed_data import check_schema


def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def unit(name, *, peer=None):
    owner = "module." + name
    entities = [
        {
            "id": f"entity.{name}.service",
            "title": f"{name.upper()} service",
            "kind": "program",
            "meaning": f"#entity.{name}.service",
        }
    ]
    definitions = f'<a id="entity.{name}.service"></a>\n\nThe service performs the admitted action.\n'
    diagram = f'    service["{name.upper()} service"]\n'
    dependencies = []
    agreement = ""
    if peer:
        entities.append(
            {
                "id": f"entity.{name}.{peer}",
                "title": peer.upper(),
                "kind": "used module",
                "meaning": f"#entity.{name}.{peer}",
                "target_id": "module." + peer,
            }
        )
        definitions += f'\n<a id="entity.{name}.{peer}"></a>\n\n{peer.upper()} supplies admission outcomes.\n'
        diagram += f'    peer["{peer.upper()}"]\n    service -->|uses| peer\n'
        dependencies.append(
            {"target_id": "module." + peer, "meaning": "#local-provider"}
        )
        agreement = "\n### Provider agreement {#local-provider}\n\nUse the provider for admission; stop on rejection.\n"
    reading = (
        f"# {name.upper()}\n\n## Purpose\n\nPerform the admitted {name} responsibility.\n"
        "\n## Terminology\n\nNo specialized terminology.\n\n## Usage\n\nSubmit one request; rejected input produces no result.\n"
        "\n## Design\n\nAdmission precedes state changes.\n\n"
        + definitions
        + "\n## Relationships\n\nThis view shows the admission collaboration only.\n\n"
        "```mermaid\nflowchart LR\n" + diagram + "```\n" + agreement
    )
    metadata = {
        "schema_version": 2,
        "document": {"id": f"document.{name}.module", "owner": owner, "role": "module"},
        "entities": entities,
        "dependencies": dependencies,
        "bindings": [],
    }
    return reading, metadata


def fixture(root):
    sources = {}
    targets = []
    for name in ("a", "b", "c"):
        reading, metadata = unit(name, peer="b" if name == "a" else None)
        path = f"specs/{name}/module.md"
        sources[path] = reading.encode()
        sources[metadata_path(path)] = encoded(metadata)
        precise = f"specs/{name}/obligations.md"
        sources[precise] = (
            f"# {name.upper()} obligations\n\n### req.{name}.once — At most one result\n\n"
            f"{name.upper()} SHALL create at most one result per admitted request.\n\n"
            f"### scenario.{name}.act — Admitted request\n\n"
            "- GIVEN a valid request\n- WHEN it is submitted\n- THEN one result is returned\n"
        ).encode()
        sources[metadata_path(precise)] = encoded(
            {
                "schema_version": 2,
                "document": {
                    "id": f"document.{name}.obligations",
                    "owner": "module." + name,
                    "role": "implementation",
                },
                "entities": [],
                "dependencies": [],
                "bindings": [],
            }
        )
        targets.append(
            {
                "id": "module." + name,
                "kind": "module",
                "title": name.upper(),
                "documents": [path, precise],
                "references": [],
                "parent": None,
                "uses": ["module.b"] if name == "a" else [],
                "files": [],
                "checks": [],
            }
        )
    interface = "specs/b/interface.md"
    definition = {
        "id": "contract.b.result",
        "version": 1,
        "schema": {"type": "boolean"},
        "semantics": "Whether admission succeeded.",
        "example": True,
    }
    sources[interface] = (
        "# Shared admission result\n\n```concorde-contract\n"
        + json.dumps(definition)
        + "\n```\n\n### Provider duties {#provider-duties}\n\n"
        "Return the canonical result for each request and do not hide rejection.\n"
    ).encode()
    sources[metadata_path(interface)] = encoded(
        {
            "schema_version": 2,
            "document": {
                "id": "document.b.interface",
                "owner": "module.b",
                "role": "implementation",
            },
            "entities": [],
            "dependencies": [],
            "bindings": [
                {
                    "id": "contract.b.result",
                    "version": 1,
                    "role": "provided",
                    "peer": "module.a",
                    "meaning": "#provider-duties",
                }
            ],
        }
    )
    targets[1]["documents"].append(interface)
    targets[0]["references"] = [
        {"kind": "module", "id": "module.b"},
        {"kind": "document", "id": "document.b.interface"},
    ]
    targets[1]["references"] = [{"kind": "module", "id": "module.c"}]
    targets[2]["references"] = [{"kind": "module", "id": "module.a"}]
    a_metadata = json.loads(sources["specs/a/module.md.json"])
    a_metadata["bindings"] = [
        {
            "id": "contract.b.result",
            "version": 1,
            "role": "required",
            "peer": "module.b",
            "meaning": "#consumer-duties",
        }
    ]
    sources["specs/a/module.md.json"] = encoded(a_metadata)
    sources["specs/a/module.md"] += (
        b"\n### Consumer duties {#consumer-duties}\n\n"
        b"Use the [canonical result](../b/interface.md#contract.b.result) during admission. "
        b"React to rejection without changing state.\n"
    )
    registry = {
        "schema_version": 5,
        "project_id": "project.example",
        "entry_target": "module.a",
        "targets": targets,
        "checks": [],
    }
    sources[".concorde/specs.json"] = encoded(registry)
    for path, raw in sources.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    (root / "secret.py").write_text("UNSELECTED_IMPLEMENTATION = True\n")
    return registry


class DocumentUnitRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry = fixture(self.root)

    def repository(self):
        return DocumentUnitRepository(self.root)

    def save(self):
        (self.root / ".concorde/specs.json").write_bytes(encoded(self.registry))

    def change(self, path, update):
        file = self.root / path
        raw = file.read_bytes()
        content = (
            update(json.loads(raw)) if path.endswith(".json") else update(raw.decode())
        )
        text = encoded(content).decode() if path.endswith(".json") else content
        return {"path": path, "before_digest": digest(raw), "content": text}

    def test_terminology_links_require_admitted_canonical_definitions_not_forwarders(
        self,
    ):
        topic = self.root / "specs/a/module.md"
        definition = self.root / "specs/b/module.md"
        original = definition.read_text()
        definition.write_text(
            original.replace(
                "No specialized terminology.",
                "| Term | Meaning / definition |\n| --- | --- |\n| Reservation | Stock held before checkout. |",
            )
        )
        topic_original = topic.read_text()
        for meaning in (
            "Defined by B.",
            "Stock held before checkout. Source: B.",
            "Stock set aside before checkout. Source: B.",
        ):
            with self.subTest(meaning=meaning):
                topic.write_text(
                    topic_original.replace(
                        "No specialized terminology.",
                        "| Term | Meaning / definition |\n| --- | --- |\n"
                        f"| [Reservation](../b/module.md#terminology) | {meaning} |",
                    )
                )
                self.repository().validate()
        # A local restatement neither replaces the source nor relaxes its context checks.
        before = self.repository().spec_context("module.a")
        definition.write_text(
            definition.read_text().replace(
                "Stock held before checkout.", "Stock held until cancellation."
            )
        )
        with self.assertRaisesRegex(SpecError, "stale"):
            self.repository().recheck_resolution(before)
        self.registry["targets"][0]["references"] = [
            {"kind": "document", "id": "document.b.interface"}
        ]
        self.save()
        with self.assertRaisesRegex(SpecError, "terminology definition outside"):
            self.repository().validate()
        self.registry["targets"][0]["references"].append(
            {"kind": "module", "id": "module.b"}
        )
        self.save()
        definition.write_text(
            original.replace(
                "No specialized terminology.",
                "| Term | Meaning / definition |\n| --- | --- |\n| [Reservation](../c/module.md#terminology) | Stock set aside before checkout. Source: C. |",
            )
        )
        with self.assertRaisesRegex(SpecError, "no local canonical definition"):
            self.repository().validate()

    def test_one_level_reference_resolves_complete_pairs_once_with_provenance(self):
        repository = self.repository()
        repository.validate()
        resolution = repository.spec_context("module.a").value
        paths = [record["path"] for record in resolution["sources"]]
        expected = [
            "specs/a/module.md",
            "specs/a/module.md.json",
            "specs/a/obligations.md",
            "specs/a/obligations.md.json",
            "specs/b/interface.md",
            "specs/b/interface.md.json",
            "specs/b/module.md",
            "specs/b/module.md.json",
            "specs/b/obligations.md",
            "specs/b/obligations.md.json",
        ]
        self.assertEqual(expected, paths)
        self.assertEqual(expected, list(repository.spec_files("module.a")))
        self.assertEqual(
            ["specs/a/module.md", "specs/a/obligations.md"], resolution["documents"]
        )
        self.assertTrue(
            all(
                "main_visible" not in record and "content" not in record
                for record in resolution["sources"]
            )
        )
        paired = [
            record
            for record in resolution["sources"]
            if record["document_id"] == "document.b.interface"
        ]
        self.assertEqual({"reading", "metadata"}, {record["role"] for record in paired})
        self.assertEqual(paired[0]["reasons"], paired[1]["reasons"])
        self.assertEqual(
            [
                {"kind": "document", "id": "document.b.interface"},
                {"kind": "module", "id": "module.b"},
            ],
            paired[0]["reasons"],
        )
        self.assertNotIn(
            "specs/c/module.md",
            paths,
            "references of included providers must not recurse",
        )

    def test_document_reference_includes_only_that_unit_and_keeps_its_owner(self):
        self.registry["targets"][0]["references"] = [
            {"kind": "document", "id": "document.b.interface"}
        ]
        self.save()
        repository = self.repository()
        repository.validate()
        resolution = repository.spec_context("module.a")
        self.assertEqual(6, len(resolution.value["sources"]))
        self.assertNotIn("specs/b/module.md", repository.spec_files("module.a"))
        self.assertEqual(
            ("module.a", "module.b"), repository.context_users("document.b.interface")
        )
        self.assertTrue(
            all(
                source["owner"] == "module.b"
                for source in resolution.value["sources"]
                if source["document_id"] == "document.b.interface"
            )
        )

    def test_scenario_query_uses_sole_owner_context_not_the_consumers_context(self):
        repository = self.repository()
        scenario = repository.spec_context("scenario.b.act").value
        self.assertEqual("module.b", scenario["module_id"])
        self.assertEqual("scenario", scenario["query_kind"])
        self.assertEqual("specs/b/module.md", scenario["reading_entry"])
        self.assertIn(
            "specs/c/module.md.json", [s["path"] for s in scenario["sources"]]
        )
        self.assertNotIn("specs/a/module.md", [s["path"] for s in scenario["sources"]])
        for query in ("document.b.interface", "entity.b.service", "req.b.once"):
            with self.subTest(query=query), self.assertRaises(SpecError):
                repository.spec_context(query)

    def test_metadata_index_does_not_read_unselected_human_bodies(self):
        from concorde.spec.repository import read_file

        observed = []

        def observe(root, path):
            observed.append(path)
            if path == "specs/c/module.md":
                raise AssertionError("unselected body read")
            return read_file(root, path)

        with patch("concorde.spec.content_repository.read_file", side_effect=observe):
            repository = self.repository()
            self.assertFalse(any(path.endswith(".md") for path in observed))
            repository.spec_context("module.a")
        self.assertIn(
            "specs/c/module.md.json",
            observed,
            "identity lookup may inspect only the declared metadata",
        )

    def test_host_materializes_exact_pairs_and_never_implementation_or_recursive_sources(
        self,
    ):
        repository = self.repository()
        resolution = repository.spec_context("module.a")
        value = {"protocol": [], "spec_resolution": resolution.value}
        granted = context_documents(repository, value)
        self.assertEqual(set(granted), set(context_grants(value)))
        self.assertEqual(granted, repository.context_bytes(resolution))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            materialize_documents(destination, granted)
            for path, raw in granted.items():
                self.assertEqual(raw, (destination / path).read_bytes())
            self.assertFalse((destination / "secret.py").exists())
            self.assertFalse((destination / "specs/c/module.md").exists())
        policy = compile_policy(
            EffectDeclaration(
                reads=("spec-context", "implementation"), writes=("implementation",)
            ),
            PolicyBinding(
                "concorde-implement",
                "implementation",
                0,
                "programmer",
                "programmer",
                write_roles=("implementation",),
            ),
            {"spec-context": tuple(granted), "implementation": ("src/owned.py",)},
        )
        self.assertEqual(("src/owned.py",), policy.write_paths)
        self.assertTrue(set(granted).issubset(policy.read_paths))
        self.assertFalse(set(granted).intersection(policy.write_paths))

    def test_missing_partner_wrong_role_duplicate_or_forged_identity_rejects_grants(
        self,
    ):
        repository = self.repository()
        original = repository.spec_context("module.a").value
        broken = []
        for role in ("reading", "metadata"):
            value = copy.deepcopy(original)
            value["sources"] = [s for s in value["sources"] if s["role"] != role]
            broken.append(value)
        for field, replacement in (
            ("role", "reading"),
            ("owner", "module.foreign"),
            ("document_id", "document.fake"),
            ("reasons", [{"kind": "owned", "id": "module.foreign"}]),
        ):
            value = copy.deepcopy(original)
            value["sources"][1][field] = replacement
            broken.append(value)
        value = copy.deepcopy(original)
        value["sources"].append(copy.deepcopy(value["sources"][0]))
        broken.append(value)
        for value in broken:
            with self.subTest(sources=value["sources"]), self.assertRaises(SpecError):
                context_documents(
                    repository, {"protocol": [], "spec_resolution": value}
                )
        with self.assertRaises(SpecError):
            repository.source_bytes("secret.py")

    def test_missing_malformed_or_symlink_metadata_fails_without_partial_resolution(
        self,
    ):
        path = self.root / "specs/b/interface.md.json"
        before = path.read_bytes()
        for raw in (None, b"{}", b'{"schema_version":1,"schema_version":1}'):
            with self.subTest(raw=raw):
                if raw is None:
                    path.unlink()
                else:
                    path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    self.repository()
                path.write_bytes(before)
        path.unlink()
        path.symlink_to(self.root / "specs/a/module.md.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.repository()
        path.unlink()
        path.write_bytes(before)
        reading = self.root / "specs/b/interface.md"
        reading.unlink()
        reading.hardlink_to(self.root / "specs/a/module.md")
        with self.assertRaisesRegex(ValueError, "physical source alias"):
            self.repository()

    def test_both_members_are_excluded_from_implementation_and_external_material(self):
        for member in ("specs/b/interface.md", "specs/b/interface.md.json"):
            for field in ("files", "references"):
                value = copy.deepcopy(self.registry)
                if field == "files":
                    value["targets"][0]["files"] = [member]
                else:
                    value["targets"][0]["references"].append(
                        {"kind": "external", "path": member}
                    )
                with (
                    self.subTest(member=member, field=field),
                    self.assertRaises(ValueError),
                ):
                    DocumentUnitRepository(self.root, registry_bytes=encoded(value))

    def test_registry_only_files_cannot_widen_an_implementation_grant(self):
        registry = copy.deepcopy(self.registry)
        registry["targets"][0]["files"] = ["secret.py"]
        repository = DocumentUnitRepository(self.root, registry_bytes=encoded(registry))
        target = repository.select("module.a")
        for query in (
            repository.implementation_entries,
            repository.implementation_paths,
            repository.implementation_files,
        ):
            with (
                self.subTest(query=query.__name__),
                self.assertRaisesRegex(SpecError, "entries differ"),
            ):
                query(target)

    def test_metadata_only_changes_invalidate_owner_and_direct_consumers(self):
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        path = "specs/b/interface.md.json"
        original = (self.root / path).read_bytes()
        (self.root / path).write_bytes(original + b"\n")
        with self.assertRaisesRegex(SpecError, "stale"):
            repository.recheck_resolution(baseline)
        with self.assertRaisesRegex(SpecError, "changed"):
            context_documents(
                repository, {"protocol": [], "spec_resolution": baseline.value}
            )
        self.assertEqual(
            ("module.a", "module.b"), repository.affected_contexts(self.repository())
        )
        self.assertNotIn(
            "module.c",
            repository.affected_contexts(self.repository()),
            "consumer references must not recurse",
        )

    def test_reference_changes_invalidate_even_when_source_path_set_is_unchanged(self):
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        self.registry["targets"][0]["references"].pop()
        self.save()
        current = self.repository()
        self.assertEqual(
            repository.spec_files("module.a"), current.spec_files("module.a")
        )
        with self.assertRaises(SpecError):
            repository.recheck_resolution(baseline)

    def test_review_change_extraction_includes_metadata_without_code_reads(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.test",
                "commit",
                "-qm",
                "Base",
            ],
            check=True,
        )
        path = self.root / "specs/b/interface.md.json"
        path.write_bytes(path.read_bytes() + b"\n")
        repository = self.repository()
        changes = _changes(repository, repository.select("module.a"), "spec", "HEAD")
        self.assertEqual(
            ["specs/b/interface.md.json"], [change["path"] for change in changes]
        )
        self.assertNotIn("UNSELECTED_IMPLEMENTATION", str(changes))
        # A finding names the canonical reading document, while its precise location may be
        # the metadata member. Included provider ownership is retained, not reassigned to A.
        from types import SimpleNamespace

        from concorde.review.review import _validate

        snapshot = SimpleNamespace(id=digest("snapshot"))
        info = {"review_mode": "spec", "input_digest": digest("review")}
        from concorde.issues.reporting import IssueReporter
        from tests.concorde.issues.test_store import report, source

        reporter = IssueReporter(
            self.root,
            source(target_id="module.a", context_id=snapshot.id),
            frozenset({"module.a", "module.b"}),
            frozenset(repository.spec_files("module.a")),
        )
        observation = report(
            owner_target_id="module.b",
            evidence=[
                {
                    "path": "specs/b/interface.md.json",
                    "description": "Clarify participant mapping.",
                }
            ],
        )
        ref = reporter(observation)["receipt"]
        data = {
            "context_id": snapshot.id,
            "input_digest": info["input_digest"],
            "review_mode": "spec",
            "status": "findings",
            "answer": "Metadata observation.",
            "representative_tasks": ["Review admission"],
            "issues": [
                {**ref, "severity": "advisory", "affected_task": "Review admission"}
            ],
        }
        run = SimpleNamespace(
            repository=repository, target=repository.select("module.a")
        )
        _validate(run, snapshot, info, data)
        observation["evidence"][0]["path"] = "specs/c/module.md.json"
        with self.assertRaisesRegex(SpecError, "scope"):
            reporter(observation)

    def test_a_scoped_diagram_can_omit_an_inventory_entity_but_not_invent_one(self):
        path = self.root / "specs/a/module.md"
        path.write_text(
            path.read_text()
            + '\n<a id="entity.a.note"></a>\n\nA diagnostic note retained for support.\n'
        )
        meta_path = self.root / "specs/a/module.md.json"
        metadata = json.loads(meta_path.read_bytes())
        metadata["entities"].append(
            {
                "id": "entity.a.note",
                "title": "Support note",
                "kind": "record",
                "meaning": "#entity.a.note",
            }
        )
        meta_path.write_bytes(encoded(metadata))
        self.repository().validate()
        path.write_text(
            path.read_text().replace(
                'service["A service"]', 'service["Invented service"]'
            )
        )
        with self.assertRaisesRegex(SpecError, "unknown"):
            self.repository().validate()

    def test_resolution_wire_shape_is_closed_and_has_no_presentation_fields(self):
        value = self.repository().spec_context("module.a").value
        check_schema(value, unit_resolution_schema())
        self.assertEqual(self.registry["targets"][0], value["registration"])
        for field, replacement in (
            ("role", "implementation"),
            ("main_visible", True),
            ("content", "injected body"),
        ):
            changed = copy.deepcopy(value)
            changed["sources"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_schema(changed, unit_resolution_schema())

    def test_canonical_contract_examples_are_opaque_and_real_examples_are_validated(
        self,
    ):
        path = self.root / "specs/b/interface.md"
        original = path.read_text()
        path.write_text(
            original
            + '\n````markdown\n```concorde-contract\n{"id":"not.a.definition"}\n```\n````\n'
        )
        repository = self.repository()
        repository.validate()
        self.assertEqual(
            ["contract.b.result"],
            [
                c["id"]
                for c in repository.context_contracts(repository.select("module.a"))
            ],
        )
        path.write_text(original.replace('"example": true', '"example": "invalid"'))
        with self.assertRaises(ValueError):
            self.repository().validate()

    def test_new_topology_units_require_both_members_in_the_candidate_overlay(self):
        registry = copy.deepcopy(self.registry)
        target = {
            "id": "module.d",
            "kind": "module",
            "title": "D",
            "documents": ["specs/d/module.md"],
            "references": [],
            "parent": None,
            "uses": [],
            "files": [],
            "checks": [],
        }
        registry["targets"].append(target)
        reading, metadata = unit("d")
        overrides = {"specs/d/module.md": reading.encode()}
        with self.assertRaisesRegex(SpecError, "member is missing"):
            DocumentUnitRepository(
                self.root,
                registry_bytes=encoded(registry),
                document_overrides=overrides,
            )
        overrides["specs/d/module.md.json"] = encoded(metadata)
        candidate = DocumentUnitRepository(
            self.root, registry_bytes=encoded(registry), document_overrides=overrides
        )
        candidate.validate()
        self.assertEqual(set(overrides), set(candidate.spec_files("module.d")))
        self.assertFalse((self.root / "specs/d").exists())

    def test_discovery_pool_keeps_complete_pairs_and_one_copy_of_shared_sources(self):
        repository = self.repository()
        selected = [
            repository.spec_context(name).value for name in ("module.a", "module.b")
        ]
        pool = {
            record["path"]: {
                key: value for key, value in record.items() if key != "reasons"
            }
            for resolution in selected
            for record in resolution["sources"]
        }
        value = {"protocol": [], "documents": [pool[path] for path in sorted(pool)]}
        granted = context_documents(repository, value)
        self.assertEqual(14, len(granted))
        self.assertEqual(set(granted), set(context_grants(value)))
        self.assertEqual(
            1, sum(path == "specs/b/interface.md.json" for path in granted)
        )
        self.assertIn(
            "specs/c/module.md.json",
            granted,
            "B explicitly selected C in its own context",
        )

    def test_entire_checkout_is_admitted_through_the_bound_document_unit_repository(
        self,
    ):
        root = Path(__file__).resolve().parents[3]
        repository = SpecRepository(root)
        repository.validate()
        self.assertEqual(15, repository.config["profile_version"])
        self.assertEqual("10.0.0", repository.config["protocol"]["version"])
        self.assertEqual(len(repository.targets), len(repository.context_identities()))
        self.assertEqual(
            2 * len(repository.document_targets), len(repository.source_documents)
        )
        for path in repository.document_targets:
            self.assertTrue((root / metadata_path(path)).is_file())

    def test_old_registry_is_not_an_automatic_compatibility_input(self):
        self.registry["schema_version"] = 4
        self.save()
        with self.assertRaisesRegex(SpecError, "schema 5"):
            self.repository()
        with self.assertRaises(ValueError):
            SpecRepository(
                self.root
            )  # no bound active Framework config was created by this backend

    def test_local_agreements_require_included_definitions(self):
        self.registry["targets"][0]["references"] = []
        self.save()
        with self.assertRaisesRegex(SpecError, "excluded definition"):
            self.repository().validate()

    def test_contract_version_pairing_and_global_identity_uniqueness(self):
        path = self.root / "specs/b/interface.md.json"
        original = json.loads(path.read_bytes())
        changed = copy.deepcopy(original)
        changed["bindings"][0]["version"] = 2
        path.write_bytes(encoded(changed))
        with self.assertRaisesRegex(SpecError, "binding|version"):
            self.repository().validate()
        changed = copy.deepcopy(original)
        changed["document"]["id"] = "document.a.module"
        path.write_bytes(encoded(changed))
        with self.assertRaisesRegex(SpecError, "duplicate document identity"):
            self.repository()

    def test_context_resolution_errors_are_stale_but_unrelated_errors_propagate(self):
        def fail(error):
            @_stale_on_resolution_error
            def run():
                raise error

            return run

        for error in (ValueError("invalid"), OSError("gone")):
            with self.subTest(error=error), self.assertRaises(SpecError) as caught:
                fail(error)()
            self.assertEqual("stale_context", caught.exception.code)
        error = SpecError("already stale", "stale_context")
        with self.assertRaises(SpecError) as caught:
            fail(error)()
        self.assertIs(error, caught.exception)
        with self.assertRaises(RuntimeError):
            fail(RuntimeError("programmer error"))()

    def test_author_overlay_validates_both_changes_together_then_applies_atomically(
        self,
    ):
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        changes = [
            self.change(
                "specs/a/module.md",
                lambda text: text.replace("entity.a.service", "entity.a.coordinator"),
            ),
            self.change(
                "specs/a/module.md.json",
                lambda value: {
                    **value,
                    "entities": [
                        {
                            **value["entities"][0],
                            "id": "entity.a.coordinator",
                            "meaning": "#entity.a.coordinator",
                        },
                        value["entities"][1],
                    ],
                },
            ),
        ]
        with self.assertRaises(ValueError):
            author_candidate(repository, "module.a", changes[:1], baseline=baseline)
        candidate = author_candidate(repository, "module.a", changes, baseline=baseline)
        self.assertIn(
            "entity.a.coordinator",
            candidate.definitions(candidate.select("module.a")).anchors,
        )
        self.assertNotIn(
            "entity.a.coordinator", (self.root / "specs/a/module.md").read_text()
        )
        value = {
            "protocol": [],
            "spec_resolution": candidate.spec_context("module.a").value,
        }
        granted = context_documents(repository, value, candidate_repository=candidate)
        self.assertIn(b"entity.a.coordinator", granted["specs/a/module.md.json"])
        self.assertEqual(
            [c["path"] for c in changes],
            apply_author_changes(repository, "module.a", changes, baseline=baseline),
        )
        self.repository().validate()

    def test_foreign_metadata_stale_inputs_and_identity_reassignment_are_rejected(self):
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        foreign = self.change("specs/b/interface.md.json", lambda value: value)
        with self.assertRaisesRegex(SpecError, "ownership"):
            author_candidate(repository, "module.a", [foreign], baseline=baseline)
        reassigned = self.change(
            "specs/a/module.md.json",
            lambda value: {
                **value,
                "document": {**value["document"], "id": "document.a.changed"},
            },
        )
        with self.assertRaisesRegex(SpecError, "document identity"):
            author_candidate(repository, "module.a", [reassigned], baseline=baseline)
        stale = self.change("specs/a/module.md", lambda text: text + "\n")
        stale["before_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SpecError, "stale"):
            apply_author_changes(repository, "module.a", [stale], baseline=baseline)

    def test_failed_transaction_restores_reading_and_metadata(self):
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        paths = ["specs/a/module.md", "specs/a/module.md.json"]
        before = {path: (self.root / path).read_bytes() for path in paths}
        changes = [
            self.change(
                paths[0],
                lambda text: text.replace(
                    "Admission precedes", "Request admission precedes"
                ),
            ),
            self.change(paths[1], lambda value: value),
        ]
        import concorde.spec.changes as transactions

        replace = transactions.os.replace
        count = 0

        def fail_second(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("second member write failed")
            return replace(source, destination)

        with (
            patch.object(transactions.os, "replace", side_effect=fail_second),
            self.assertRaises(OSError),
        ):
            apply_author_changes(repository, "module.a", changes, baseline=baseline)
        self.assertEqual(
            before, {path: (self.root / path).read_bytes() for path in paths}
        )

    def test_topology_overlay_preserves_document_identity_and_reconciles_owner(self):
        # Move the same companion unit to C. All participants must still include its definition.
        before = self.repository()
        baseline = before.spec_context("module.a")
        registry = copy.deepcopy(self.registry)
        registry["targets"][1]["documents"].remove("specs/b/interface.md")
        registry["targets"][2]["documents"].append("specs/b/interface.md")
        registry["targets"][1]["references"] = [
            {"kind": "document", "id": "document.b.interface"}
        ]
        # The new owner supplies B's previous provided role; reconcile the counterpart atomically.
        b = json.loads((self.root / "specs/b/interface.md.json").read_bytes())
        b["document"]["owner"] = "module.c"
        a = json.loads((self.root / "specs/a/module.md.json").read_bytes())
        a["bindings"][0]["peer"] = "module.c"
        candidate = DocumentUnitRepository(
            self.root,
            registry_bytes=encoded(registry),
            document_overrides={
                "specs/b/interface.md.json": encoded(b),
                "specs/a/module.md.json": encoded(a),
            },
        )
        candidate.validate()
        self.assertEqual(
            "document.b.interface", candidate.unit("specs/b/interface.md").document_id
        )
        self.assertEqual("module.c", candidate.unit("specs/b/interface.md").owner)
        self.assertEqual(
            ("module.a", "module.b", "module.c"), before.affected_contexts(candidate)
        )
        self.assertEqual(
            baseline.serialized,
            before.spec_context("module.a").serialized,
            "overlay cannot mutate its base",
        )
        self.assertTrue(
            candidate.source_is_overridden("specs/b/interface.md"),
            "a metadata-only override selects the candidate for both source members",
        )
        # Exercise the actual topology author source assembler with an explicit test Protocol
        # index. This is not installation/profile admission or a worker launch.
        from concorde.harness.context import (
            PROTOCOL_PATHS,
            resolve_topology_author_context,
        )

        before.protocol_assets = dict.fromkeys(
            PROTOCOL_PATHS, b"Test Protocol index source\n"
        )
        before.config = {
            "protocol": {"version": "8.0.0", "digest": digest("test binding")}
        }
        snapshot = resolve_topology_author_context(
            before,
            registry["targets"][2],
            task="Transfer interface ownership",
            instructions="Read only owned and explicitly included units.",
            workspace={},
            candidate_repository=candidate,
        )
        records = [
            record
            for record in snapshot.value["spec_resolution"]["sources"]
            if record["document_id"] == "document.b.interface"
        ]
        self.assertEqual(2, len(records))
        self.assertTrue(all(record["owner"] == "module.c" for record in records))
        granted = context_documents(
            before, snapshot.value, candidate_repository=candidate
        )
        self.assertEqual(encoded(b), granted["specs/b/interface.md.json"])

    def test_pending_confirmation_edits_only_metadata_and_keeps_missing_entries(self):
        path = self.root / "specs/a/module.md.json"
        value = json.loads(path.read_bytes())
        value["entities"][0].update(
            files=["src/a.py", "src/future.py"], pending=["src/a.py", "src/future.py"]
        )
        path.write_bytes(encoded(value))
        self.registry["targets"][0]["files"] = ["src/a.py", "src/future.py"]
        self.save()
        (self.root / "src").mkdir()
        (self.root / "src/a.py").write_text(
            "IMPLEMENTATION_NOT_IN_SPEC_CONTEXT = True\n"
        )
        repository = self.repository()
        baseline = repository.spec_context("module.a")
        before = (self.root / "specs/a/module.md").read_bytes()
        changes, confirmed, missing = pending_changes(repository)
        self.assertEqual(["specs/a/module.md.json"], [c["path"] for c in changes])
        self.assertEqual(["src/future.py"], missing)
        self.assertEqual(1, len(confirmed))
        self.assertEqual((confirmed, missing), confirm_pending_units(repository))
        self.assertEqual(before, (self.root / "specs/a/module.md").read_bytes())
        self.assertEqual(
            ["src/future.py"],
            self.repository()
            .unit("specs/a/module.md")
            .declarations["entities"][0]["pending"],
        )
        with self.assertRaises(SpecError):
            repository.recheck_resolution(baseline)
        self.assertEqual(([], missing), confirm_pending_units(self.repository()))


if __name__ == "__main__":
    unittest.main()
