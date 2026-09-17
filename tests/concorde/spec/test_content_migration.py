"""Explicit migration preserves promises without claiming to finish semantic editing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from concorde.spec.content_migration import (
    plan_document_migration,
    preview_registered_migration,
)
from concorde.spec.content_model import ContentModelError
from concorde.spec.repository import digest


OWNER = "module.checkout"
DOCUMENT = {"id": "document.checkout.module", "owner": OWNER, "main_visible": True}
ENTITIES = [
    {
        "id": "entity.checkout.service",
        "title": "Checkout service",
        "kind": "program",
        "responsibility": "Reserve stock before creating an order.",
        "files": ["src/checkout/"],
        "pending": ["src/checkout/"],
    },
    {
        "id": "entity.checkout.inventory",
        "title": "Inventory",
        "kind": "used module",
        "responsibility": "Maintain reservations independently of order storage.",
        "target_id": "module.inventory",
    },
]
DEPENDENCY = {
    "target_id": "module.inventory",
    "responsibility": "Maintain available stock and reservations.",
    "selection_condition": "When admitting a submitted cart.",
    "relied_upon_promises": [
        "[Reservation outcome](inventory.md#scenario.inventory.reserve) decides admission.",
        "A reservation rejection leaves stock unchanged.",
    ],
}
BINDING = {
    "id": "contract.inventory.reserve",
    "version": 3,
    "role": "required",
    "peer": "module.inventory",
    "selection_condition": "When the submitted cart contains items requiring reservation.",
    "relied_upon_guarantees": ["An explicit rejection is not a transport failure."],
    "obligations": [
        "Supply positive quantities.",
        "Preserve the request ID on transport retry.",
    ],
}
CONTRACT = {
    "id": "contract.checkout.result",
    "version": 1,
    "schema": {"type": "boolean"},
    "semantics": "Whether admission succeeded.",
    "example": True,
}


def block(name, value):
    return "```" + name + "\n" + json.dumps(value, indent=2) + "\n```\n"


def source():
    return (
        block("concorde-document", DOCUMENT)
        + "\n# Checkout\n\n## Usage & Contract\n\n### Purpose\n\nAdmit one customer order.\n"
        "\n### Usage\n\nSubmit a cart; rejection creates no order.\n"
        "\n### Requirements\n\n#### req.checkout.once — At most one order\n\n"
        "Checkout SHALL create at most one order per admitted request.\n"
        "\n### Scenarios\n\n#### scenario.checkout.reject — Rejected cart\n\n"
        "- GIVEN insufficient stock\n- WHEN the cart is submitted\n- THEN no order is created\n"
        "\n## Architecture & Realization\n\n### Design\n\nReserve before recording the order.\n"
        "\n### Entities\n\nThe coordinator stores orders; Inventory has independent ownership.\n\n"
        + block("concorde-entities", ENTITIES)
        + "\n### Relationships\n\nThis view shows reservation admission, not the storage schema.\n\n"
        '```mermaid\nflowchart LR\n    service["Checkout service"]\n    inventory["Inventory"]\n'
        "    service -->|reserves through| inventory\n```\n"
        "\n### Dependencies\n\n"
        + block("concorde-dependencies", [DEPENDENCY])
        + "\n### Boundary\n\n"
        + block("concorde-contract", CONTRACT)
        + "\n"
        + block("concorde-contract-binding", BINDING)
    )


def migrate(text=None, primary=True):
    path = "specs/checkout/module.md" if primary else "specs/checkout/details.md"
    return plan_document_migration(
        path,
        (source() if text is None else text).encode(),
        expected_owner=OWNER,
        primary=primary,
    )


class ContentMigrationTests(unittest.TestCase):
    def test_complete_recorded_meaning_moves_to_reading_once_without_file_inventory(
        self,
    ):
        plan = migrate()
        reading = "\n".join(unit.reading.content.decode() for unit in plan.units)
        metadata = plan.unit.declarations
        self.assertEqual(DOCUMENT["id"], plan.unit.document_id)
        self.assertEqual(OWNER, plan.unit.owner)
        self.assertEqual(["src/checkout/"], metadata["entities"][0]["files"])
        self.assertEqual(["src/checkout/"], metadata["entities"][0]["pending"])
        self.assertNotIn("src/checkout/", reading)
        self.assertNotIn("## Entities", reading)
        self.assertNotIn("Usage & Contract", reading)
        self.assertNotIn("Architecture & Realization", reading)
        self.assertEqual(
            ["Purpose", "Usage", "Design", "Relationships"],
            [line[3:] for line in reading.splitlines() if line.startswith("## ")][:4],
        )
        self.assertIn(
            "The coordinator stores orders",
            reading,
            "ordinary source prose must not disappear",
        )
        for item in plan.preserved_meanings:
            with self.subTest(category=item.category, field=item.field):
                self.assertIn(item.text, reading)
                self.assertNotIn(item.text, plan.unit.metadata.content.decode())
        self.assertEqual(10, len(plan.preserved_meanings))
        self.assertIn("req.checkout.once — At most one order", reading)
        self.assertIn("- THEN no order is created", reading)
        self.assertIn(block("concorde-contract", CONTRACT), reading)

    def test_semantics_are_reachable_from_metadata_not_copied_into_it(self):
        plan = migrate()
        metadata = plan.unit.declarations
        for entity in metadata["entities"]:
            meaning = plan.unit.meaning(entity["meaning"]).text
            original = next(e for e in ENTITIES if e["id"] == entity["id"])
            self.assertIn(original["responsibility"], meaning)
        meaning = plan.unit.meaning(metadata["dependencies"][0]["meaning"]).text
        self.assertIn(DEPENDENCY["selection_condition"], meaning)
        for promise in DEPENDENCY["relied_upon_promises"]:
            self.assertIn(promise, meaning)
        binding_unit = next(
            unit for unit in plan.units if unit.declarations["bindings"]
        )
        meaning = binding_unit.meaning(
            binding_unit.declarations["bindings"][0]["meaning"]
        ).text
        for promise in [*BINDING["relied_upon_guarantees"], *BINDING["obligations"]]:
            self.assertIn(promise, meaning)

    def test_migration_report_is_explicitly_not_applied_or_semantically_complete(self):
        plan = migrate()
        self.assertEqual(digest(source().encode()), plan.before_digest)
        self.assertFalse(plan.report["applied"])
        self.assertEqual("not_completed", plan.report["semantic_rewrite"])
        self.assertTrue(plan.editorial_notes)
        self.assertEqual(plan.report, migrate().report)

    def test_companions_do_not_acquire_the_entry_template(self):
        text = (
            block("concorde-document", DOCUMENT)
            + "\n# Boundary\n\n## Usage & Contract\n\nUse this admission agreement.\n\n"
            + block("concorde-contract", CONTRACT)
            + "\n## Architecture & Realization\n\n### Locking\n\nHold the lock until commit.\n"
        )
        plan = migrate(text, primary=False)
        reading = plan.unit.reading.content.decode()
        self.assertNotIn("## Purpose", reading)
        self.assertIn("## Design\n\n### Locking", reading)
        self.assertIn("Hold the lock until commit.", reading)
        self.assertEqual([], plan.unit.declarations["entities"])

    def test_fenced_examples_and_diagram_bytes_are_preserved(self):
        text = (
            source()
            + "\n#### Example\n\n````markdown\n## Usage & Contract\n```concorde-entities\n[]\n```\n````\n"
        )
        for primary in (True, False):
            with self.subTest(primary=primary):
                plan = migrate(text, primary=primary)
                self.assertIn(
                    "````markdown\n## Usage & Contract\n```concorde-entities\n[]\n```\n````",
                    "\n".join(unit.reading.content.decode() for unit in plan.units),
                )
        self.assertIn(
            "    service -->|reserves through| inventory",
            migrate().unit.reading.content.decode(),
        )
        # ATX closing markers and trailing whitespace are accepted by the old format. Migration
        # removes their actual outer headings, but must leave identical example lines untouched.
        variants = (
            source()
            .replace("## Usage & Contract\n", "## Usage & Contract ##  \n")
            .replace(
                "## Architecture & Realization\n",
                "## Architecture & Realization ##  \n",
            )
        )
        self.assertNotIn(
            "Usage & Contract", migrate(variants).unit.reading.content.decode()
        )

    def test_a_missing_relationship_explanation_remains_a_real_reading_gap(self):
        text = source().replace(
            "This view shows reservation admission, not the storage schema.", ""
        )
        with self.assertRaisesRegex(
            ContentModelError, "Relationships requires explanatory prose"
        ):
            migrate(text)

    def test_unknown_machine_fields_are_not_discarded(self):
        for name, old, changed in (
            (
                "concorde-entities",
                ENTITIES,
                [{**ENTITIES[0], "security": "must not be lost"}, ENTITIES[1]],
            ),
            (
                "concorde-dependencies",
                [DEPENDENCY],
                [{**DEPENDENCY, "obligations": ["keep me"]}],
            ),
            (
                "concorde-contract-binding",
                BINDING,
                {**BINDING, "schema": {"type": "string"}},
            ),
        ):
            text = source().replace(block(name, old), block(name, changed))
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ContentModelError, "cannot be discarded"),
            ):
                migrate(text)

    def test_unknown_profile_inventories_are_preserved_and_flagged_for_classification(
        self,
    ):
        text = (
            source()
            + "\n### Capability inventory\n\n"
            + block("concorde-custom-control", [{"id": "submit"}])
        )
        plan = migrate(text)
        self.assertIn(
            block("concorde-custom-control", [{"id": "submit"}]),
            plan.unit.reading.content.decode(),
        )
        self.assertTrue(
            any("concorde-custom-control" in note for note in plan.editorial_notes)
        )

    def test_known_framework_inventories_move_to_named_metadata_extensions(self):
        for language, key in [
            ("concorde-capabilities", "concorde.capabilities"),
            ("concorde-agents", "concorde.agents"),
        ]:
            entries = [{"id": "example", "public": False}]
            plan = migrate(source() + "\n### Inventory\n\n" + block(language, entries))
            self.assertEqual(entries, plan.unit.declarations["extensions"][key])
            self.assertNotIn("```" + language, plan.unit.reading.content.decode())
            self.assertFalse(plan.report["applied"])
            self.assertEqual("not_completed", plan.report["semantic_rewrite"])

    def test_old_visibility_is_not_reinterpreted_as_reading_membership(self):
        text = source().replace(
            block("concorde-document", DOCUMENT),
            block("concorde-document", {**DOCUMENT, "main_visible": False}),
        )
        plan = migrate(text)
        self.assertFalse(plan.legacy_main_visible)
        self.assertNotIn("main_visible", plan.unit.declarations["document"])
        self.assertTrue(
            any("publisher configuration" in note for note in plan.editorial_notes)
        )
        self.assertIn(
            "SHALL", "\n".join(unit.reading.content.decode() for unit in plan.units)
        )

    def test_obsolete_prose_and_links_are_flagged_not_silently_reinterpreted(self):
        plan = migrate(
            source().replace(
                "Reserve before recording the order.",
                "Profile 13 has two-part reading. See [design](other.md#architecture--realization).",
            )
        )
        self.assertTrue(
            any("previous Protocol" in note for note in plan.editorial_notes)
        )
        self.assertTrue(
            any("links to removed" in note for note in plan.editorial_notes)
        )
        self.assertIn(
            "other.md#architecture--realization", plan.unit.reading.content.decode()
        )

    def test_new_format_is_not_read_as_legacy_runtime_compatibility(self):
        with self.assertRaisesRegex(ContentModelError, "invalid migration source"):
            migrate(migrate().unit.reading.content.decode())

    def test_wrong_ownership_duplicate_headers_and_unclosed_fences_fail_closed(self):
        for text in (
            source().replace('"owner": "module.checkout"', '"owner": "module.foreign"'),
            block("concorde-document", DOCUMENT) + source(),
            source() + "\n```json\n{}",
        ):
            with self.subTest(text=text[-30:]), self.assertRaises(ValueError):
                migrate(text)


class RegisteredMigrationPreviewTests(unittest.TestCase):
    def test_activated_checkout_refuses_repeated_legacy_conversion_without_writes(self):
        root = Path(__file__).resolve().parents[3]
        registry = json.loads((root / ".concorde/specs.json").read_text())
        paths = [
            member
            for target in registry["targets"]
            for path in target["documents"]
            for member in (path, path + ".json")
        ]
        before = {path: (root / path).read_bytes() for path in paths}
        with self.assertRaisesRegex(ContentModelError, "legacy registry schema 4"):
            preview_registered_migration(root)
        self.assertEqual(before, {path: (root / path).read_bytes() for path in paths})

    def test_missing_or_invalid_members_block_preview_without_claiming_partial_success(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".concorde").mkdir()
            (root / "specs").mkdir()
            path = "specs/module.md"
            registry = {
                "schema_version": 4,
                "targets": [{"id": OWNER, "documents": [path]}],
            }
            (root / ".concorde/specs.json").write_text(json.dumps(registry))
            report = preview_registered_migration(root)
            self.assertEqual("blocked", report["status"])
            self.assertFalse(report["ready_to_apply"])
            self.assertEqual(path, report["errors"][0]["path"])
            (root / path).write_text(
                source().replace(
                    "This view shows reservation admission, not the storage schema.", ""
                )
            )
            report = preview_registered_migration(root)
            self.assertEqual("blocked", report["status"])
            self.assertIn(
                "Relationships requires explanatory prose",
                report["errors"][0]["message"],
            )

    def test_registration_never_discovers_neighbors_or_accepts_duplicate_ownership(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".concorde").mkdir()
            (root / "specs").mkdir()
            (root / "specs/module.md").write_text(source())
            (root / "specs/undeclared.md").write_text("Not a registered Spec.")
            target = {"id": OWNER, "documents": ["specs/module.md"]}
            registry = {"schema_version": 4, "targets": [target]}
            path = root / ".concorde/specs.json"
            path.write_text(json.dumps(registry))
            self.assertEqual(
                1, preview_registered_migration(root)["registered_documents"]
            )
            registry["targets"].append(
                {"id": "module.other", "documents": ["specs/module.md"]}
            )
            path.write_text(json.dumps(registry))
            with self.assertRaisesRegex(
                ContentModelError, "duplicate document registration"
            ):
                preview_registered_migration(root)
            for version in (5, 4.0, True):
                registry = {"schema_version": version, "targets": [target]}
                path.write_text(json.dumps(registry))
                with (
                    self.subTest(version=version),
                    self.assertRaisesRegex(
                        ContentModelError, "legacy registry schema 4"
                    ),
                ):
                    preview_registered_migration(root)


if __name__ == "__main__":
    unittest.main()
