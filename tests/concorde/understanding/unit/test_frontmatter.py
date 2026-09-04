import sys
import unittest

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.frontmatter import FrontMatterError, parse_document  # noqa: E402


class FrontMatterTests(unittest.TestCase):
    def test_parses_constrained_nested_profile(self):
        source = """---
id: module.example
kind: module
children:
  - module.example.child
contracts:
  provided: []
  required:
    - contract.example.input
---
# Example
"""
        data, body = parse_document(source, "specs/example/module.md")
        self.assertEqual(data["children"], ["module.example.child"])
        self.assertEqual(data["contracts"]["provided"], [])
        self.assertEqual(data["contracts"]["required"], ["contract.example.input"])
        self.assertIn("# Example", body)

    def test_rejects_unsupported_yaml_features(self):
        for token in ("&anchor", "*alias", "!tag", "<<:"):
            with self.subTest(token=token), self.assertRaises(FrontMatterError):
                parse_document(f"---\nid: {token}\n---\nbody\n", "source.md")

    def test_requires_opening_and_closing_fences(self):
        with self.assertRaises(FrontMatterError):
            parse_document("id: module.example", "source.md")


if __name__ == "__main__":
    unittest.main()
