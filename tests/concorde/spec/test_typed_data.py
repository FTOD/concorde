from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.spec.typed_data import (
    STRING,
    TypedDataError,
    artifact,
    data_schema,
    decode,
    obj,
    register,
    type_version,
    typed,
    typed_schema,
    validate_typed,
    verify_artifacts,
)
from concorde.spec.verification import verifies


class TypedDataTests(unittest.TestCase):
    def test_artifact_references_detect_staleness_missing_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "artifact.md"
            path.write_text("original")
            reference = artifact(root, "artifact.fixture", "artifact.md")
            verify_artifacts(root, reference)
            path.write_text("modified")
            with self.assertRaisesRegex(TypedDataError, "changed"):
                verify_artifacts(root, reference)
            path.unlink()
            with self.assertRaisesRegex(TypedDataError, "does not exist"):
                verify_artifacts(root, reference)
            (root / "other.md").write_text("original")
            path.symlink_to(root / "other.md")
            with self.assertRaisesRegex(TypedDataError, "symlink"):
                verify_artifacts(root, reference)

    @verifies("scenario.spec.typed-value-accept")
    def test_a_registered_type_checks_its_values_as_copies(self):
        register("concorde-fixture-accept", 1, obj({"name": STRING}))
        data = {"name": "value"}
        value = typed("concorde-fixture-accept", data)
        self.assertEqual(
            {
                "type_id": "concorde-fixture-accept",
                "schema_version": 1,
                "data": data,
            },
            value,
        )
        self.assertIsNot(data, value["data"])
        checked = validate_typed(value, "concorde-fixture-accept")
        self.assertEqual(value, checked)
        self.assertIsNot(value, checked)
        # A schema refers to another type by name, resolved when a value is checked.
        register(
            "concorde-fixture-holder",
            1,
            obj({"inner": typed_schema("concorde-fixture-late")}),
        )
        holder = {
            "type_id": "concorde-fixture-holder",
            "schema_version": 1,
            "data": {
                "inner": {
                    "type_id": "concorde-fixture-late",
                    "schema_version": 2,
                    "data": {},
                }
            },
        }
        with self.assertRaises(TypedDataError) as raised:
            validate_typed(holder)
        self.assertEqual("unknown_type", raised.exception.code)
        register("concorde-fixture-late", 2, obj({}))
        self.assertEqual(holder, validate_typed(holder))

    @verifies("scenario.spec.typed-value-reject")
    def test_values_that_do_not_fit_their_registration_are_refused(self):
        register("concorde-fixture-reject", 1, obj({"name": STRING}))
        cases = {
            "unknown_type": (
                {"type_id": "concorde-fixture-none", "schema_version": 1, "data": {}},
                "/type_id",
            ),
            "unsupported_version": (
                {
                    "type_id": "concorde-fixture-reject",
                    "schema_version": 2,
                    "data": {"name": "x"},
                },
                "/schema_version",
            ),
            "invalid_field": (
                {
                    "type_id": "concorde-fixture-reject",
                    "schema_version": 1,
                    "data": {"name": "x", "extra": 1},
                },
                "/data/extra",
            ),
        }
        for code, (value, field) in cases.items():
            with self.subTest(code=code), self.assertRaises(TypedDataError) as raised:
                validate_typed(value)
            self.assertEqual(
                (code, field), (raised.exception.code, raised.exception.field)
            )

    @verifies("scenario.spec.typed-value-json-schema")
    def test_data_is_checked_as_json_schema_checks_it(self):
        register(
            "concorde-fixture-json-schema",
            1,
            {
                "type": "object",
                "properties": {
                    "open": {"type": "object", "properties": {"name": STRING}},
                    "closed": obj({"name": STRING}),
                    "seconds": {"type": "number", "minimum": 0},
                },
            },
        )

        def value(**data):
            return {
                "type_id": "concorde-fixture-json-schema",
                "schema_version": 1,
                "data": data,
            }

        # An object with no additionalProperties is open, the data's own object included.
        admitted = value(open={"name": "x", "other": [1]}, seconds=0, extra=True)
        self.assertEqual(admitted, validate_typed(admitted))
        for seconds in (0, 3, 0.4, 12.5):
            with self.subTest(seconds=seconds):
                self.assertEqual(
                    seconds, validate_typed(value(seconds=seconds))["data"]["seconds"]
                )
        refused = {
            "/data/closed/other": value(closed={"name": "x", "other": 1}),
            "/data/seconds": value(seconds=True),
            "/data/open/name": value(open={"name": 1}),
        }
        for seconds in (True, "0.4", -0.5, -1, None):
            refused[f"/data/seconds {seconds!r}"] = value(seconds=seconds)
        for label, data in refused.items():
            with (
                self.subTest(label=label),
                self.assertRaises(TypedDataError) as raised,
            ):
                validate_typed(data)
            self.assertEqual(
                ("invalid_field", label.split(" ")[0]),
                (raised.exception.code, raised.exception.field),
            )

    def test_keywords_follow_json_schema(self):
        from concorde.spec.typed_data import check_schema

        admitted = [
            ("ab", {"pattern": "b"}),
            (1, {"type": "number", "maximum": 1}),
            ({"a": 1}, {"type": "object", "additionalProperties": {"type": "integer"}}),
            (["x"], {"type": "array", "maxItems": 1}),
            ("x", {"minLength": 1}),
            (5, {"minLength": 1, "properties": {}}),
            ({"a": "b"}, True),
            (1.0, {"enum": [1, 2]}),
            ([1], {"const": [1.0]}),
            ([1, 2], {"type": "array", "uniqueItems": True}),
            (12, {"anyOf": [{"type": "integer"}], "minimum": 10}),
        ]
        refused = [
            ("ab", {"pattern": "^b"}),
            (2, {"type": "number", "maximum": 1}),
            (1.5, {"type": "integer"}),
            (float("nan"), {"type": "number"}),
            ({"a": "b"}, {"additionalProperties": {"type": "integer"}}),
            (["x", "y"], {"type": "array", "maxItems": 1}),
            ("xyz", {"type": "string", "maxLength": 2}),
            (" ", {"type": "string", "minLength": 1}),
            (True, {"enum": [1, 2]}),
            (1, {"const": True}),
            ([1], {"const": [True]}),
            ({"a": [True]}, {"enum": [{"a": [1]}]}),
            ([1, 1.0], {"type": "array", "uniqueItems": True}),
            ([{"a": 1}, {"a": 1.0}], {"type": "array", "uniqueItems": True}),
            (1, {"anyOf": [{"type": "integer"}], "minimum": 10}),
            ({"a": 1}, {"additionalProperties": False}),
            ("x", False),
        ]
        for data, schema in admitted:
            with self.subTest(data=data, schema=schema):
                check_schema(data, schema)
        for data, schema in refused:
            with (
                self.subTest(data=data, schema=schema),
                self.assertRaises(TypedDataError) as raised,
            ):
                check_schema(data, schema)
            self.assertEqual("invalid_field", raised.exception.code)

    def test_the_contract_subset_compares_json_values(self):
        from concorde.spec.schema import ContractError, validate

        for data, schema in (
            (1, {"const": 1.0}),
            (2.0, {"enum": [1, 2]}),
            ([1, 2], {"type": "array", "uniqueItems": True}),
        ):
            with self.subTest(data=data, schema=schema):
                validate(data, schema)
        for data, schema in (
            ([1], {"const": [True]}),
            (True, {"enum": [1]}),
            ([1, 1.0], {"type": "array", "uniqueItems": True}),
        ):
            with (
                self.subTest(data=data, schema=schema),
                self.assertRaises(ContractError),
            ):
                validate(data, schema)

    @verifies("scenario.spec.typed-register-conflict")
    def test_a_second_registration_must_be_identical(self):
        schema = obj({"name": STRING})
        register("concorde-fixture-conflict", 1, schema)
        register("concorde-fixture-conflict", 1, obj({"name": STRING}))
        for version, other in ((2, schema), (1, obj({"other": STRING}))):
            with (
                self.subTest(version=version),
                self.assertRaises(TypedDataError) as raised,
            ):
                register("concorde-fixture-conflict", version, other)
            self.assertEqual("duplicate_type", raised.exception.code)
        self.assertEqual(1, type_version("concorde-fixture-conflict"))
        self.assertEqual(schema, data_schema("concorde-fixture-conflict"))
        with self.assertRaises(TypedDataError):
            register("concorde-fixture-bad", 1, {"type": "object", "unknown": True})
        # A keyword the checker would not evaluate is refused, so no type promises more.
        for schema in (
            {"oneOf": [STRING]},
            {"allOf": [STRING]},
            {"$defs": {"a": STRING}, "$ref": "#/$defs/a"},
            {"$schema": "https://json-schema.org/draft/2020-12/schema", **STRING},
            {"$id": "https://example.com/note", **STRING},
            obj({"a": {"type": ["string", "null"]}}),
            obj({"a": {"anyOf": [{"type": "null"}, {"allOf": [STRING]}]}}),
        ):
            with (
                self.subTest(schema=schema),
                self.assertRaises(TypedDataError) as raised,
            ):
                register("concorde-fixture-unchecked", 1, schema)
            self.assertEqual("invalid_input", raised.exception.code)
        # A property may be named like a keyword.
        register("concorde-fixture-keyword-names", 1, obj({"oneOf": STRING}))
        # A property named $ref and literal data holding $ref are no type references.
        register(
            "concorde-fixture-ref-names",
            1,
            obj({"$ref": STRING, "kind": {"const": {"$ref": "x"}}}),
        )

    @verifies("scenario.spec.typed-value-reject")
    def test_json_rejects_duplicate_fields_and_non_finite_numbers(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                decode(value)


if __name__ == "__main__":
    unittest.main()
