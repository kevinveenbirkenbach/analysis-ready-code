# tests/unit/test_cli.py
import os
import sys
import unittest
from unittest.mock import patch

# Ensure src/ is on sys.path when running via discover
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from arc.cli import parse_arguments  # noqa: E402


class TestCliParseArguments(unittest.TestCase):
    def test_basic_paths_and_defaults(self):
        with patch.object(sys, "argv", ["arc", "foo", "bar"]):
            args = parse_arguments()

        self.assertEqual(args.paths, ["foo", "bar"])
        self.assertEqual(args.file_types, [])
        self.assertEqual(args.ignore_file_strings, [])
        self.assertFalse(args.clipboard)
        self.assertFalse(args.quiet)
        # show_hidden default is False → ignore_hidden should be True
        self.assertFalse(args.show_hidden)
        self.assertTrue(args.ignore_hidden)

    def test_clipboard_and_quiet_short_flags(self):
        with patch.object(sys, "argv", ["arc", ".", "-x", "-q"]):
            args = parse_arguments()

        self.assertTrue(args.clipboard)
        self.assertTrue(args.quiet)

    def test_ignore_file_strings_short_and_long(self):
        # Test only the short form -I collecting multiple values
        with patch.object(
            sys,
            "argv",
            ["arc", ".", "-I", "build", "dist", "node_modules"],
        ):
            args = parse_arguments()

        self.assertEqual(
            args.ignore_file_strings,
            ["build", "dist", "node_modules"],
        )

    def test_show_hidden_switches_ignore_hidden_off(self):
        with patch.object(sys, "argv", ["arc", ".", "--show-hidden"]):
            args = parse_arguments()

        self.assertTrue(args.show_hidden)
        self.assertFalse(args.ignore_hidden)


if __name__ == "__main__":
    unittest.main()
