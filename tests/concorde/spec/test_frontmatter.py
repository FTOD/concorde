from __future__ import annotations

import sys
import unittest

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.spec.frontmatter import FrontMatterError, parse_document


def document(*lines: str) -> str:
    return "\n".join(("---", *lines, "---", "Body")) + "\n"


class FrontMatterTests(unittest.TestCase):
    def test_punctuation_inside_scalars_is_text(self):
        metadata, body = parse_document(
            document('title: "Ready!"', "team: R&D", "note: a *b* c", "q: 'x & y'")
        )
        self.assertEqual(
            {"title": "Ready!", "team": "R&D", "note": "a *b* c", "q": "x & y"},
            metadata,
        )
        self.assertEqual("Body\n", body)

    def test_tags_anchors_aliases_and_merge_keys_are_refused(self):
        for line in ("a: &anchor x", "a: *alias", "a: !tag x", "<<: x"):
            with self.subTest(line=line), self.assertRaises(FrontMatterError) as raised:
                parse_document(document(line), "doc.md")
            self.assertIn("unsupported YAML tag", str(raised.exception))
            self.assertEqual(2, raised.exception.line)

    def test_duplicate_keys_are_refused_with_their_line(self):
        cases = {
            'a: {"k": 1, "k": 2}': 2,
            'a: [{"k": 1, "k": 2}]': 2,
        }
        for line, number in cases.items():
            with self.subTest(line=line), self.assertRaises(FrontMatterError) as raised:
                parse_document(document(line), "doc.md")
            self.assertEqual(number, raised.exception.line)
        with self.assertRaises(FrontMatterError) as raised:
            parse_document(document("items:", "  - a: 1", "    b: 2", "    a: 3"), "d")
        self.assertEqual(5, raised.exception.line)
        self.assertIn("duplicate key 'a'", str(raised.exception))
        metadata, _ = parse_document(
            document("items:", "  - a: 1", "    b:", "      a: 2")
        )
        self.assertEqual({"items": [{"a": 1, "b": {"a": 2}}]}, metadata)


if __name__ == "__main__":
    unittest.main()
