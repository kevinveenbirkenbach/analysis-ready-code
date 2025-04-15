import re
import zlib

class CodeProcessor:
    PYTHON = ".py"
    JS = ".js"
    C = ".c"
    CPP = ".cpp"
    H = ".h"
    BASH = ".sh"
    SHELL = ".bash"

    @staticmethod
    def remove_comments(content, file_type):
        """Remove comments based on file type."""
        comment_patterns = {
            CodeProcessor.PYTHON: [
                (r'\s*#.*', '', 0),
                (r'\"\"\"(.*?)\"\"\"', '', re.DOTALL),
                (r"\'\'\'(.*?)\'\'\'", '', re.DOTALL)
            ],
            CodeProcessor.JS: [
                (r'\s*//.*', '', 0),
                (r'/\*.*?\*/', '', 0)
            ],
            CodeProcessor.C: [
                (r'\s*//.*', '', 0),
                (r'/\*.*?\*/', '', 0)
            ],
            CodeProcessor.CPP: [
                (r'\s*//.*', '', 0),
                (r'/\*.*?\*/', '', 0)
            ],
            CodeProcessor.H: [
                (r'\s*//.*', '', 0),
                (r'/\*.*?\*/', '', 0)
            ],
            CodeProcessor.BASH: [
                (r'\s*#.*', '', 0)
            ],
            CodeProcessor.SHELL: [
                (r'\s*#.*', '', 0)
            ]
        }

        patterns = comment_patterns.get(file_type, [])
        for pattern, repl, flags in patterns:
            content = re.sub(pattern, repl, content, flags=flags)
        return content.strip()

    @staticmethod
    def compress(content):
        """Compress code using zlib."""
        return zlib.compress(content.encode())