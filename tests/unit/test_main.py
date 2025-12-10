# tests/unit/test_main.py
import io
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# Ensure src/ is on sys.path when running via discover
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

import arc  # noqa: E402


class TestArcMain(unittest.TestCase):
    def _make_args(
        self,
        path,
        clipboard=False,
        quiet=False,
        file_types=None,
        ignore_file_strings=None,
        ignore_hidden=True,
        verbose=False,
        no_comments=False,
        compress=False,
        path_contains=None,
        content_contains=None,
        no_gitignore=False,
        scan_binary_files=False,
    ):
        return types.SimpleNamespace(
            paths=[path],
            clipboard=clipboard,
            quiet=quiet,
            file_types=file_types or [],
            ignore_file_strings=ignore_file_strings or [],
            ignore_hidden=ignore_hidden,
            show_hidden=not ignore_hidden,
            verbose=verbose,
            no_comments=no_comments,
            compress=compress,
            path_contains=path_contains or [],
            content_contains=content_contains or [],
            no_gitignore=no_gitignore,
            scan_binary_files=scan_binary_files,
        )

    @patch("arc.subprocess.run")
    @patch("arc.DirectoryHandler.handle_directory")
    @patch("arc.parse_arguments")
    def test_main_clipboard_calls_xclip_and_uses_tee(
        self, mock_parse_arguments, mock_handle_directory, mock_run
    ):
        # create a temporary directory as scan target
        with tempfile.TemporaryDirectory() as tmpdir:
            args = self._make_args(path=tmpdir, clipboard=True, quiet=False)
            mock_parse_arguments.return_value = args

            def fake_handle_directory(path, **kwargs):
                out = kwargs["output_stream"]
                # should be a Tee instance
                self.assertEqual(out.__class__.__name__, "Tee")
                out.write("FROM ARC\n")

            mock_handle_directory.side_effect = fake_handle_directory

            buf = io.StringIO()
            with redirect_stdout(buf):
                arc.main()

        # stdout should contain the text once (via Tee -> sys.stdout)
        stdout_value = buf.getvalue()
        self.assertIn("FROM ARC", stdout_value)

        # xclip should have been called with the same text in input
        mock_run.assert_called_once()
        called_args, called_kwargs = mock_run.call_args
        self.assertEqual(called_args[0], ["xclip", "-selection", "clipboard"])
        self.assertIn("FROM ARC", called_kwargs.get("input", ""))

    @patch("arc.subprocess.run")
    @patch("arc.DirectoryHandler.handle_directory")
    @patch("arc.parse_arguments")
    def test_main_clipboard_quiet_only_clipboard_no_stdout(
        self, mock_parse_arguments, mock_handle_directory, mock_run
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = self._make_args(path=tmpdir, clipboard=True, quiet=True)
            mock_parse_arguments.return_value = args

            def fake_handle_directory(path, **kwargs):
                out = kwargs["output_stream"]
                # quiet + clipboard → output_stream is a buffer (StringIO)
                self.assertIsInstance(out, io.StringIO)
                out.write("SILENT CONTENT\n")

            mock_handle_directory.side_effect = fake_handle_directory

            buf = io.StringIO()
            # stdout should stay empty
            with redirect_stdout(buf):
                arc.main()

        stdout_value = buf.getvalue()
        self.assertEqual(stdout_value, "")

        mock_run.assert_called_once()
        called_args, called_kwargs = mock_run.call_args
        self.assertEqual(called_args[0], ["xclip", "-selection", "clipboard"])
        self.assertIn("SILENT CONTENT", called_kwargs.get("input", ""))

    @patch("arc.DirectoryHandler.handle_directory")
    @patch("arc.parse_arguments")
    def test_main_quiet_without_clipboard_uses_nullwriter(
        self, mock_parse_arguments, mock_handle_directory
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = self._make_args(path=tmpdir, clipboard=False, quiet=True)
            mock_parse_arguments.return_value = args

            def fake_handle_directory(path, **kwargs):
                out = kwargs["output_stream"]
                # quiet without clipboard → internal NullWriter class
                self.assertEqual(out.__class__.__name__, "NullWriter")
                # writing should not raise
                out.write("SHOULD NOT APPEAR ANYWHERE\n")

            mock_handle_directory.side_effect = fake_handle_directory

            buf = io.StringIO()
            with redirect_stdout(buf):
                arc.main()

        # Nothing should be printed to stdout
        self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
