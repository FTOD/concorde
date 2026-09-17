"""The next Protocol's document-unit primitives; these do not activate the new runtime profile."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.content_model import (
    ContentModelError,
    admit_document_unit,
    load_document_unit,
    metadata_path,
    reading_meanings,
    reading_problems,
)
from concorde.spec.verification import verifies

READING = """# Checkout

## Purpose

Checkout admits an order for a customer without overselling available inventory.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Reservation | Stock held for a submitted cart before an order is created. |

## Usage

Submit a cart once. A rejected reservation creates no order; retry with a new decision.

## Design

Reservation precedes order creation so a failed admission cannot create a partial order.

<a id="entity.checkout.service"></a>

**Checkout service** coordinates reservation and records an admitted order atomically.

<a id="entity.checkout.inventory"></a>

**Inventory** supplies stock reservation without becoming Checkout's structural child.

## Relationships

This overview shows admission collaboration, not every record in the implementation inventory.

```mermaid
flowchart LR
    service["Checkout service"]
    inventory["Inventory"]
    service -->|reserves through| inventory
```

### Reservation collaboration {#checkout-inventory-agreement}

Inventory maintains reservations. Use it when admitting a cart. Rely on the canonical
[reservation outcome](inventory.md#scenario.inventory.reserve); a rejected reservation leaves no
order. Checkout must supply positive quantities and react to insufficient stock without retrying.

### Reservation participation {#checkout-reservation-obligations}

Require the [reservation agreement](inventory.md#contract.inventory.reserve) when admitting a cart.
Rely on the result to decide whether to proceed. Supply positive quantities, preserve request
identity on transport retry and never turn an explicit rejection into a successful order.

"""

PRECISE = """# Checkout obligations

## Requirements

### req.checkout.single-order — One order per submission

Checkout SHALL create at most one order for an admitted submission.

## Scenarios

### scenario.checkout.rejected — Reservation rejection creates no order

- GIVEN insufficient stock
- WHEN the customer submits the cart
- THEN no order is created
"""

METADATA = {
    "schema_version": 2,
    "document": {
        "id": "document.checkout.module",
        "owner": "module.checkout",
        "role": "module",
    },
    "entities": [
        {
            "id": "entity.checkout.service",
            "title": "Checkout service",
            "kind": "program",
            "meaning": "#entity.checkout.service",
            "files": ["src/checkout/"],
            "pending": [],
        },
        {
            "id": "entity.checkout.inventory",
            "title": "Inventory",
            "kind": "used module",
            "meaning": "#entity.checkout.inventory",
            "target_id": "module.inventory",
        },
    ],
    "dependencies": [
        {"target_id": "module.inventory", "meaning": "#checkout-inventory-agreement"},
    ],
    "bindings": [
        {
            "id": "contract.inventory.reserve",
            "version": 1,
            "role": "required",
            "peer": "module.inventory",
            "meaning": "#checkout-reservation-obligations",
        },
    ],
}


def encode(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def admit(reading=READING, metadata=None, primary=True):
    return admit_document_unit(
        "specs/checkout/module.md",
        reading.encode(),
        encode(METADATA if metadata is None else metadata),
        expected_owner="module.checkout",
        primary=primary,
    )


class DocumentUnitTests(unittest.TestCase):
    @verifies("scenario.spec.document-roles")
    def test_roles_are_explicit_and_formal_definitions_are_module_owned_precise_content(
        self,
    ):
        for role in (None, False, [], {}, "topic", ""):
            metadata = copy.deepcopy(METADATA)
            metadata["document"]["role"] = role
            with self.subTest(role=role), self.assertRaises(ContentModelError):
                admit(metadata=metadata)
        metadata = copy.deepcopy(METADATA)
        del metadata["document"]["role"]
        with self.assertRaises(ContentModelError):
            admit(metadata=metadata)
        metadata = copy.deepcopy(METADATA)
        metadata["extensions"] = {"concorde.publication": {"collection": "module"}}
        with self.assertRaisesRegex(ContentModelError, "retired concorde.publication"):
            admit(metadata=metadata)
        metadata = copy.deepcopy(METADATA)
        metadata["document"]["role"] = "implementation"
        with self.assertRaisesRegex(ContentModelError, "module.md must have"):
            admit(metadata=metadata)
        for path, primary in [
            ("specs/checkout/module.md", True),
            ("specs/checkout/topic.md", False),
        ]:
            with (
                self.subTest(path=path),
                self.assertRaisesRegex(ContentModelError, "implementation-role"),
            ):
                admit_document_unit(
                    path,
                    (READING + PRECISE).encode(),
                    encode(METADATA),
                    expected_owner="module.checkout",
                    primary=primary,
                )
        # Examples and links do not declare a second formal obligation.
        admit(READING + "\n````markdown\n" + PRECISE + "\n````\n")

    def test_reading_is_one_member_of_complete_content_not_a_generated_summary(self):
        unit = admit()
        self.assertEqual(READING.encode(), unit.reading.content)
        self.assertEqual(encode(METADATA), unit.metadata.content)
        self.assertEqual(
            ("reading", "metadata"), tuple(source.role for source in unit.sources)
        )
        self.assertEqual(
            ("specs/checkout/module.md", "specs/checkout/module.md.json"),
            tuple(source.path for source in unit.sources),
        )
        self.assertEqual("document.checkout.module", unit.document_id)
        self.assertEqual("module.checkout", unit.owner)
        self.assertNotIn("src/checkout/", unit.reading.content.decode())
        self.assertIn(
            "preserve request", unit.meaning("#checkout-reservation-obligations").text
        )
        self.assertNotIn("preserve request", unit.metadata.content.decode())
        precise = admit_document_unit(
            "specs/checkout/obligations.md",
            PRECISE.encode(),
            encode(
                {
                    "schema_version": 2,
                    "document": {
                        "id": "document.checkout.obligations",
                        "owner": "module.checkout",
                        "role": "implementation",
                    },
                    "entities": [],
                    "dependencies": [],
                    "bindings": [],
                }
            ),
            expected_owner="module.checkout",
        )
        self.assertIn("SHALL", precise.meaning("#req.checkout.single-order").text)
        self.assertIn(
            "THEN no order", precise.meaning("#scenario.checkout.rejected").text
        )

    def test_metadata_and_reading_bytes_independently_bind_identity(self):
        original = admit()
        edited = copy.deepcopy(METADATA)
        edited["entities"][0]["pending"] = ["src/checkout/"]
        self.assertNotEqual(original.identity, admit(metadata=edited).identity)
        self.assertEqual(original.reading.digest, admit(metadata=edited).reading.digest)
        self.assertNotEqual(
            original.identity,
            admit(READING.replace("without retrying", "by reporting failure")).identity,
        )
        reordered = admit_document_unit(
            "specs/checkout/module.md",
            READING.encode(),
            json.dumps(METADATA, sort_keys=True).encode(),
            expected_owner="module.checkout",
            primary=True,
        )
        self.assertEqual(original.declarations, reordered.declarations)
        self.assertNotEqual(
            original.identity,
            reordered.identity,
            "digests identify exact bytes, not normalized JSON",
        )
        self.assertEqual(original.identity, admit().identity)

    def test_admitted_sources_cannot_be_mutated_through_declaration_views(self):
        unit = admit()
        value = unit.declarations
        value["entities"][0]["files"].append("secret.py")
        self.assertEqual(METADATA, unit.declarations)
        self.assertEqual(admit().identity, unit.identity)

    def test_meaning_is_derived_from_reading_and_stops_at_the_next_anchor(self):
        unit = admit()
        text = unit.meaning("#entity.checkout.service").text
        self.assertIn("records an admitted order", text)
        self.assertNotIn("Inventory", text)
        self.assertNotIn("Relationships", text)
        self.assertNotIn(
            "reservation participation",
            unit.meaning("#checkout-inventory-agreement").text.lower(),
        )

    def test_no_io_or_undeclared_link_following_during_admission(self):
        with patch(
            "builtins.open", side_effect=AssertionError("unexpected filesystem read")
        ):
            unit = admit()
        self.assertIn(
            "inventory.md#scenario.inventory.reserve",
            unit.meaning("#checkout-inventory-agreement").text,
        )

    def test_explicit_pair_loading_and_missing_metadata_are_not_partial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "specs/checkout/module.md"
            path.parent.mkdir(parents=True)
            path.write_bytes(READING.encode())
            with self.assertRaisesRegex(ValueError, "missing.*module.md.json"):
                load_document_unit(
                    root,
                    "specs/checkout/module.md",
                    expected_owner="module.checkout",
                    primary=True,
                )
            Path(str(path) + ".json").write_bytes(encode(METADATA))
            (path.parent / "unregistered.md").write_text("No reader may discover me.")
            unit = load_document_unit(
                root,
                "specs/checkout/module.md",
                expected_owner="module.checkout",
                primary=True,
            )
            self.assertEqual(admit().identity, unit.identity)
            with self.assertRaisesRegex(ContentModelError, "owner differs"):
                load_document_unit(
                    root, "specs/checkout/module.md", expected_owner="module.foreign"
                )

    def test_symlink_reading_metadata_and_parent_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real").mkdir()
            (root / "real/module.md").write_bytes(READING.encode())
            (root / "real/module.md.json").write_bytes(encode(METADATA))
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                load_document_unit(
                    root / "alias", "module.md", expected_owner="module.checkout"
                )
            (root / "module.md").symlink_to(root / "real/module.md")
            for path in ("alias/module.md", "module.md"):
                with (
                    self.subTest(path=path),
                    self.assertRaisesRegex(ValueError, "symlink"),
                ):
                    load_document_unit(root, path, expected_owner="module.checkout")
            (root / "module.md").unlink()
            (root / "module.md").write_bytes(READING.encode())
            (root / "module.md.json").symlink_to(root / "real/module.md.json")
            with self.assertRaisesRegex(ValueError, "symlink"):
                load_document_unit(root, "module.md", expected_owner="module.checkout")

    def test_companion_filename_is_safe_and_deterministic(self):
        self.assertEqual("specs/topic.md.json", metadata_path("specs/topic.md"))
        for path in (
            "/etc/passwd",
            "../topic.md",
            "specs//topic.md",
            "specs/./topic.md",
            "specs\\topic.md",
            "specs/topic.json",
            ".concorde/topic.md",
            ".git/topic.md",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                metadata_path(path)

    def test_metadata_shape_and_json_are_closed_and_versioned(self):
        cases = []
        for version in (True, 0, 1, 3, "2"):
            cases.append({**METADATA, "schema_version": version})
        cases.extend(
            [
                {**METADATA, "main_visible": True},
                {key: value for key, value in METADATA.items() if key != "bindings"},
                {
                    **METADATA,
                    "document": {**METADATA["document"], "main_visible": True},
                },
                {**METADATA, "entities": {}},
                {**METADATA, "dependencies": None},
                {**METADATA, "bindings": "none"},
                {
                    **METADATA,
                    "document": {"id": "module.checkout", "owner": "module.checkout"},
                },
            ]
        )
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ContentModelError):
                admit(metadata=value)
        for raw in (
            b'{"schema_version": 1, "schema_version": 1}',
            b'{"x": NaN}',
            b"\xff",
        ):
            with self.subTest(raw=raw), self.assertRaises(ContentModelError):
                admit_document_unit(
                    "specs/checkout/module.md",
                    READING.encode(),
                    raw,
                    expected_owner="module.checkout",
                )

    def test_old_inline_inventories_are_rejected_not_silently_hidden(self):
        for name in (
            "concorde-document",
            "concorde-entities",
            "concorde-dependencies",
            "concorde-contract-binding",
        ):
            for marker in ("```", "~~~~"):
                with (
                    self.subTest(name=name, marker=marker),
                    self.assertRaisesRegex(ContentModelError, "metadata"),
                ):
                    admit(READING + f"\n{marker}{name}\n{{}}\n{marker}\n")
        # A fenced example remains opaque, including examples of retired representations.
        admit(READING + "\n````markdown\n```concorde-entities\n[]\n```\n````\n")

    def test_reading_meanings_cannot_be_remote_or_borrowed_from_examples(self):
        for reference in (
            "inventory.md#meaning",
            "https://example.test/#meaning",
            "#missing",
            "",
            None,
        ):
            value = copy.deepcopy(METADATA)
            value["dependencies"][0]["meaning"] = reference
            with (
                self.subTest(reference=reference),
                self.assertRaises(ContentModelError),
            ):
                admit(metadata=value)
        fake = '\n```html\n<a id="missing"></a>\nA fictitious promise.\n```\n'
        value = copy.deepcopy(METADATA)
        value["dependencies"][0]["meaning"] = "#missing"
        with self.assertRaisesRegex(ContentModelError, "missing reading meaning"):
            admit(READING + fake, value)

    def test_entity_meanings_cannot_be_copied_into_metadata(self):
        for field in ("responsibility", "description", "semantics"):
            value = copy.deepcopy(METADATA)
            value["entities"][0][field] = "Coordinates reservation."
            with self.subTest(field=field), self.assertRaises(ContentModelError):
                admit(metadata=value)
        value = copy.deepcopy(METADATA)
        value["entities"][0]["meaning"] = "#checkout-inventory-agreement"
        with self.assertRaisesRegex(ContentModelError, "stable identity anchor"):
            admit(metadata=value)

    def test_entity_binding_invariants_are_retained_without_a_reading_inventory(self):
        for changes in (
            {"files": []},
            {"files": ["src/checkout/", "src/checkout/"]},
            {"files": ["../outside.py"]},
            {"files": [".concorde/config.json"]},
            {"files": ["specs/checkout/module.md"]},
            {"files": ["specs/checkout/module.md.json"]},
            {"files": ["specs/"]},
            {"pending": ["src/unlisted/"]},
            {"target_id": "module.inventory"},
            {"id": "document.checkout.module"},
        ):
            value = copy.deepcopy(METADATA)
            value["entities"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ContentModelError):
                admit(metadata=value)
        value = copy.deepcopy(METADATA)
        value["entities"][1]["title"] = "Checkout service"
        with self.assertRaisesRegex(ContentModelError, "duplicate entity title"):
            admit(metadata=value)
        value = copy.deepcopy(METADATA)
        value["entities"].append(copy.deepcopy(value["entities"][0]))
        with self.assertRaisesRegex(ContentModelError, "entity identity"):
            admit(metadata=value)

    def test_dependency_and_participant_identity_rules_remain_mechanical(self):
        for key in ("dependencies", "bindings"):
            value = copy.deepcopy(METADATA)
            value[key].append(copy.deepcopy(value[key][0]))
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(ContentModelError, "duplicate"),
            ):
                admit(metadata=value)
        for changes in (
            {"version": True},
            {"version": 0},
            {"role": []},
            {"role": "observer"},
            {"peer": "external: "},
            {"peer": "module.checkout"},
            {"obligations": ["copied promise"]},
            {"meaning": "#absent"},
        ):
            value = copy.deepcopy(METADATA)
            value["bindings"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ContentModelError):
                admit(metadata=value)
        value = copy.deepcopy(METADATA)
        value["bindings"][0]["peer"] = "external:inventory"
        admit(metadata=value)


class ReadingStructureTests(unittest.TestCase):
    @verifies("scenario.spec.reader-parts", "scenario.spec.reader-parts-invalid")
    def test_terminology_is_early_nonempty_and_not_an_entity_inventory(self):
        for text in (
            READING.replace("## Terminology", "## Vocabulary"),
            READING.replace(
                "| Reservation | Stock held for a submitted cart before an order is created. |",
                "",
            ),
            READING.replace("Meaning / definition", "Files"),
            READING.replace("## Terminology", "### Terminology"),
        ):
            with (
                self.subTest(text=text),
                self.assertRaisesRegex(ContentModelError, "Terminology"),
            ):
                admit(text)
        example = "\n````markdown\n## Terminology\n| Term | Meaning / definition |\n| --- | --- |\n| Fake | Example only. |\n````\n"
        admit(READING + example)
        exact = "\n```mermaid\nflowchart LR\n    %% graph: example\n    a --> b\n```\n"
        with self.assertRaisesRegex(ContentModelError, "executable Graph"):
            admit(READING + exact)
        admit(READING + "\n````markdown\n" + exact + "\n````\n")

    def test_front_four_sections_are_the_reading_path_not_two_containers(self):
        self.assertEqual((), reading_problems(READING, primary=True))
        for before, after in (
            ("## Purpose", "### Purpose"),
            ("## Design", "## Architecture & Realization"),
            ("## Usage", "## Use"),
            ("## Relationships", "## Entities"),
        ):
            with self.subTest(before=before), self.assertRaises(ContentModelError):
                admit(READING.replace(before, after))
        with self.assertRaises(ContentModelError):
            admit(READING + "\n## Design\n\nSecond authority.\n")

    def test_companion_has_no_template_sections_or_presentation_visibility_flag(self):
        value = {
            "schema_version": 2,
            "document": {
                "id": "document.checkout.errors",
                "owner": "module.checkout",
                "role": "module",
            },
            "entities": [],
            "dependencies": [],
            "bindings": [],
        }
        unit = admit_document_unit(
            "specs/checkout/errors.md",
            b"# Rejection\n\nA rejected reservation creates no order.\n\n## Terminology\n\nNo specialized terminology.\n",
            encode(value),
            expected_owner="module.checkout",
        )
        self.assertEqual("reading", unit.reading.role)
        self.assertNotIn("main_visible", unit.declarations)

    def test_purpose_is_plain_prose_but_other_reading_can_include_structured_contracts(
        self,
    ):
        with self.assertRaisesRegex(ContentModelError, "Purpose must be plain prose"):
            admit(
                READING.replace(
                    "Checkout admits an order", "- Checkout admits an order"
                )
            )
        text = (
            READING
            + "\n```concorde-contract\n"
            + json.dumps(
                {
                    "id": "contract.checkout.result",
                    "version": 1,
                    "schema": {"type": "boolean"},
                    "semantics": "Whether the order was admitted.",
                    "example": True,
                }
            )
            + "\n```\n"
        )
        with self.assertRaisesRegex(ContentModelError, "implementation-role"):
            admit(text)
        precise = {
            "schema_version": 2,
            "document": {
                "id": "document.checkout.contract",
                "owner": "module.checkout",
                "role": "implementation",
            },
            "entities": [],
            "dependencies": [],
            "bindings": [],
        }
        unit = admit_document_unit(
            "specs/checkout/contracts.md",
            text.encode(),
            encode(precise),
            expected_owner="module.checkout",
        )
        self.assertIn(b"concorde-contract", unit.reading.content)

    def test_empty_explanation_cannot_borrow_a_later_section_or_code_block(self):
        source = (
            '<a id="entity.empty"></a>\n\n<a id="entity.real"></a>\n\nReal meaning.\n'
            "\n## Other\n\nUnrelated explanation.\n"
        )
        meanings = {
            meaning.anchor: meaning.text
            for meaning in reading_meanings(source, "sample.md")
        }
        self.assertEqual("", meanings["entity.empty"])
        self.assertEqual("Real meaning.", meanings["entity.real"])
        source = source.replace("Real meaning.", "```text\nNot explanatory prose.\n```")
        self.assertEqual("", reading_meanings(source, "sample.md")[1].text)
        with self.assertRaisesRegex(ContentModelError, "empty reading meaning"):
            admit(
                READING.replace(
                    "**Checkout service** coordinates reservation and records an admitted order atomically.",
                    "",
                )
            )

    def test_duplicate_and_redirected_identity_anchors_are_invalid(self):
        for source in (
            '<a id="entity.same"></a>\nA.\n\n### More {#entity.same}\nB.\n',
            "### req.checkout.once — Once {#req.checkout.twice}\nCheckout SHALL act once.\n",
        ):
            with self.subTest(source=source), self.assertRaises(ContentModelError):
                reading_meanings(source, "sample.md")

    def test_nested_headings_stay_in_heading_meaning_but_peer_sections_do_not(self):
        source = "## Agreement {#local.agreement}\nUse the provider.\n\n### Failure\nStop on rejection.\n\n## Next\nUnrelated.\n"
        meaning = reading_meanings(source, "sample.md")[0]
        self.assertIn("Stop on rejection.", meaning.text)
        self.assertNotIn("Unrelated.", meaning.text)


if __name__ == "__main__":
    unittest.main()
