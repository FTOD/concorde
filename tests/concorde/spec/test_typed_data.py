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

    @verifies("scenario.spec.typed-value-reject")
    def test_json_rejects_duplicate_fields_and_non_finite_numbers(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                decode(value)


if __name__ == "__main__":
    unittest.main()
