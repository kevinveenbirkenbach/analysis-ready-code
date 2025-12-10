# tests/unit/test_arc.py
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

# Ensure src/ is on sys.path when running via discover
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from arc.code_processor import CodeProcessor
from arc.directory_handler import DirectoryHandler


class TestCodeProcessor(unittest.TestCase):
    def test_python_comment_and_docstring_stripping(self):
        src = '''\
"""module docstring should go away"""

# a comment
x = 1  # inline comment
y = "string with # not a comment"

def f():
    """function docstring should go away"""
    s = """triple quoted but not a docstring"""
    return x
'''
        out = CodeProcessor.remove_comments(src, ".py")
        self.assertNotIn("module docstring", out)
        self.assertNotIn("function docstring", out)
        self.assertNotIn("# a comment", out)
        # tolerate whitespace normalization from tokenize.untokenize
        self.assertRegex(out, r'y\s*=\s*"string with # not a comment"')
        self.assertIn("triple quoted but not a docstring", out)

    def test_cstyle_comment_stripping(self):
        src = '''\
// line comment
int main() {
  /* block
     comment */
  int x = 42; // end comment
  const char* s = "/* not a comment here */";
  return x;
}
'''
        out = CodeProcessor.remove_comments(src, ".c")
        # line comment and block comment gone
        self.assertNotIn("// line comment", out)
        self.assertNotIn("block\n     comment", out)
        # string content with /* */ inside should remain
        self.assertIn('const char* s = "/* not a comment here */";', out)

    def test_hash_comment_stripping(self):
        src = """\
# top comment
KEY=value  # trailing comment should be kept by default
plain: value
"""
        out = CodeProcessor.remove_comments(src, ".yml")
        # Our regex removes full lines starting with optional spaces then '#'
        self.assertNotIn("top comment", out)
        # It does not remove trailing fragments after content for hash style
        self.assertIn("KEY=value", out)
        self.assertIn("plain: value", out)

    def test_jinja_comment_stripping(self):
        src = """\
{# top jinja comment #}
Hello {{ name }}!
{#
  multi-line
  jinja comment
#}
Body text and {{ value }}.
"""
        out = CodeProcessor.remove_comments(src, ".j2")
        self.assertNotIn("top jinja comment", out)
        self.assertNotIn("multi-line", out)
        # Regular content and expressions remain
        self.assertIn("Hello {{ name }}!", out)
        self.assertIn("Body text and {{ value }}.", out)

    def test_unknown_extension_returns_stripped(self):
        src = "  x = 1  # not removed for unknown  "
        out = CodeProcessor.remove_comments(src, ".unknown")
        self.assertEqual(out, "x = 1  # not removed for unknown")

    def test_compress_decompress_roundtrip(self):
        src = "def x():\n    return 42\n"
        blob = CodeProcessor.compress(src)
        self.assertIsInstance(blob, (bytes, bytearray))
        back = CodeProcessor.decompress(blob)
        self.assertEqual(src, back)


class TestDirectoryHandler(unittest.TestCase):
    def test_is_binary_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"\x00\x01\x02BINARY")
            path = tf.name
        try:
            self.assertTrue(DirectoryHandler.is_binary_file(path))
        finally:
            os.remove(path)

    def test_gitignore_matching(self):
        with tempfile.TemporaryDirectory() as root:
            # Create .gitignore ignoring build/ and *.log
            gi_dir = os.path.join(root, "a")
            os.makedirs(gi_dir, exist_ok=True)
            with open(os.path.join(gi_dir, ".gitignore"), "w") as f:
                f.write("build/\n*.log\n")

            # Files
            os.makedirs(os.path.join(gi_dir, "build"), exist_ok=True)
            ignored_dir_file = os.path.join(gi_dir, "build", "x.txt")
            with open(ignored_dir_file, "w") as f:
                f.write("ignored")
            ignored_log = os.path.join(gi_dir, "debug.log")
            with open(ignored_log, "w") as f:
                f.write("ignored log")
            kept_file = os.path.join(gi_dir, "src.txt")
            with open(kept_file, "w") as f:
                f.write("keep me")

            gi_data = DirectoryHandler.load_gitignore_patterns(root)

            self.assertTrue(DirectoryHandler.is_gitignored(ignored_dir_file, gi_data))
            self.assertTrue(DirectoryHandler.is_gitignored(ignored_log, gi_data))
            self.assertFalse(DirectoryHandler.is_gitignored(kept_file, gi_data))

    def test_should_print_file_filters_hidden_and_types(self):
        with tempfile.TemporaryDirectory() as root:
            hidden = os.path.join(root, ".hidden.txt")
            plain = os.path.join(root, "keep.py")
            with open(hidden, "w") as f:
                f.write("data")
            with open(plain, "w") as f:
                f.write("print('hi')")

            self.assertFalse(
                DirectoryHandler.should_print_file(
                    hidden,
                    file_types=[".py"],
                    ignore_file_strings=[],
                    ignore_hidden=True,
                    path_contains=[],
                    content_contains=[],
                )
            )
            self.assertTrue(
                DirectoryHandler.should_print_file(
                    plain,
                    file_types=[".py"],
                    ignore_file_strings=[],
                    ignore_hidden=True,
                    path_contains=[],
                    content_contains=[],
                )
            )

    def test_print_file_content_no_comments_and_compress(self):
        with tempfile.TemporaryDirectory() as root:
            p = os.path.join(root, "t.py")
            with open(p, "w") as f:
                f.write("# comment only\nx=1\n")
            buf = io.StringIO()
            DirectoryHandler.print_file_content(
                p,
                no_comments=True,
                compress=False,
                output_stream=buf,
            )
            out = buf.getvalue()
            self.assertIn("<< START:", out)
            # be whitespace-tolerant (tokenize may insert spaces)
            self.assertRegex(out, r"x\s*=\s*1")
            self.assertNotIn("# comment only", out)

            buf = io.StringIO()
            DirectoryHandler.print_file_content(
                p,
                no_comments=True,
                compress=True,
                output_stream=buf,
            )
            out = buf.getvalue()
            self.assertIn("COMPRESSED CODE:", out)
            self.assertIn("<< END >>", out)


if __name__ == "__main__":
    unittest.main()
