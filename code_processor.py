import re
import zlib
from dataclasses import dataclass
from typing import Dict, Tuple, Pattern, Optional
import io
import tokenize


@dataclass(frozen=True)
class LanguageSpec:
    """Holds compiled comment patterns for a language."""
    patterns: Tuple[Pattern, ...]


class CodeProcessor:
    """
    Utilities to strip comments and (de)compress code.
    - Python: tokenize-based (safe) with precise docstring removal.
    - C/CPP/JS: state-machine comment stripper that respects string/char literals.
    - Shell/YAML: remove full-line hash comments only.
    - Jinja: remove {# ... #} blocks.
    """
    # File extensions (normalized to lowercase)
    EXT_TO_LANG: Dict[str, str] = {
        ".py": "python",
        ".js": "cstyle",
        ".c": "cstyle",
        ".cpp": "cstyle",
        ".h": "cstyle",
        ".sh": "hash",
        ".bash": "hash",
        ".yml": "hash",
        ".yaml": "hash",
        ".j2": "jinja",
        ".jinja": "jinja",
        ".jinja2": "jinja",
        ".tpl": "jinja",
    }

    # Regex-based specs for hash and jinja
    _HASH = LanguageSpec(patterns=(
        re.compile(r"^\s*#.*$", flags=re.MULTILINE),   # only full-line comments
    ))
    _JINJA = LanguageSpec(patterns=(
        re.compile(r"\{#.*?#\}", flags=re.DOTALL),     # {# ... #} across lines
    ))

    LANG_SPECS: Dict[str, LanguageSpec] = {
        "hash": _HASH,
        "jinja": _JINJA,
        # "cstyle" handled by a state machine, not regex
        # "python" handled by tokenize, not regex
    }

    @classmethod
    def _lang_from_ext(cls, file_type: str) -> Optional[str]:
        """Map an extension like '.py' to an internal language key."""
        ext = file_type.lower().strip()
        return cls.EXT_TO_LANG.get(ext)

    # -----------------------------
    # Python stripping via tokenize
    # -----------------------------
    @staticmethod
    def _strip_python_comments_tokenize(content: str) -> str:
        """
        Remove comments and docstrings safely using tokenize.
        Rules:
          - Drop COMMENT tokens.
          - Drop module docstring only if it's the very first statement at col 0.
          - Drop the first STRING statement in a suite immediately after 'def'/'class'
            header (':' NEWLINE INDENT).
        """
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        out_tokens = []

        indent_level = 0
        module_docstring_candidate = True  # until we see first real stmt at module level
        expect_suite_docstring = False     # just entered a suite after def/class
        last_was_colon = False
        seen_nontrivial_in_line = False    # guards module docstring (start of logical line)

        for tok_type, tok_str, start, end, line in tokens:
            # Track indentation
            if tok_type == tokenize.INDENT:
                indent_level += 1
            elif tok_type == tokenize.DEDENT:
                indent_level = max(0, indent_level - 1)

            # New logical line: reset guard
            if tok_type in (tokenize.NEWLINE, tokenize.NL):
                seen_nontrivial_in_line = False
                out_tokens.append((tok_type, tok_str))
                continue

            # Comments are dropped
            if tok_type == tokenize.COMMENT:
                continue

            # Detect ':' ending a def/class header
            if tok_type == tokenize.OP and tok_str == ":":
                last_was_colon = True
                out_tokens.append((tok_type, tok_str))
                continue

            # After ':' + NEWLINE + INDENT comes a suite start -> allow docstring removal
            if tok_type == tokenize.INDENT and last_was_colon:
                expect_suite_docstring = True
                last_was_colon = False
                out_tokens.append((tok_type, tok_str))
                continue
            # Any non-INDENT token clears the last_was_colon flag
            if tok_type != tokenize.NL:
                last_was_colon = False

            # STRING handling
            if tok_type == tokenize.STRING:
                at_line_start = (start[1] == 0) and not seen_nontrivial_in_line
                if indent_level == 0:
                    # Potential module docstring only if first statement at col 0
                    if module_docstring_candidate and at_line_start:
                        module_docstring_candidate = False
                        # drop it
                        continue
                    # Any other top-level string is normal
                    module_docstring_candidate = False
                    out_tokens.append((tok_type, tok_str))
                    seen_nontrivial_in_line = True
                    continue
                else:
                    # In a suite: if it's the first statement after def/class, drop regardless of column
                    if expect_suite_docstring:
                        expect_suite_docstring = False
                        # drop it
                        continue
                    expect_suite_docstring = False
                    out_tokens.append((tok_type, tok_str))
                    seen_nontrivial_in_line = True
                    continue

            # Any other significant token disables module-docstring candidacy
            if tok_type not in (tokenize.INDENT, tokenize.DEDENT):
                if indent_level == 0:
                    module_docstring_candidate = False
                # Mark we've seen something on this line
                if tok_type not in (tokenize.NL, tokenize.NEWLINE):
                    seen_nontrivial_in_line = True

            out_tokens.append((tok_type, tok_str))

        return tokenize.untokenize(out_tokens)

    # ---------------------------------
    # C-style stripping via state machine
    # ---------------------------------
    @staticmethod
    def _strip_cstyle_comments(content: str) -> str:
        """
        Remove // line comments and /* ... */ block comments while preserving
        string ("...") and char ('...') literals and their escape sequences.
        """
        i = 0
        n = len(content)
        out = []
        in_line_comment = False
        in_block_comment = False
        in_string = False
        in_char = False
        escape = False

        while i < n:
            c = content[i]
            nxt = content[i + 1] if i + 1 < n else ""

            # If inside line comment: consume until newline
            if in_line_comment:
                if c == "\n":
                    in_line_comment = False
                    out.append(c)
                i += 1
                continue

            # If inside block comment: consume until '*/'
            if in_block_comment:
                if c == "*" and nxt == "/":
                    in_block_comment = False
                    i += 2
                else:
                    i += 1
                continue

            # If inside string literal
            if in_string:
                out.append(c)
                if escape:
                    escape = False
                else:
                    if c == "\\":
                        escape = True
                    elif c == '"':
                        in_string = False
                i += 1
                continue

            # If inside char literal
            if in_char:
                out.append(c)
                if escape:
                    escape = False
                else:
                    if c == "\\":
                        escape = True
                    elif c == "'":
                        in_char = False
                i += 1
                continue

            # Not in any special state:
            # Check for start of comments
            if c == "/" and nxt == "/":
                in_line_comment = True
                i += 2
                continue
            if c == "/" and nxt == "*":
                in_block_comment = True
                i += 2
                continue

            # Check for start of string/char literals
            if c == '"':
                in_string = True
                out.append(c)
                i += 1
                continue
            if c == "'":
                in_char = True
                out.append(c)
                i += 1
                continue

            # Normal character
            out.append(c)
            i += 1

        return "".join(out)

    # -------------------
    # Public API
    # -------------------
    @classmethod
    def remove_comments(cls, content: str, file_type: str) -> str:
        """
        Remove comments based on file type/extension.
          - Python: tokenize-based
          - C/CPP/JS: state-machine
          - Hash (sh/yaml): regex full-line
          - Jinja: regex {# ... #}
        """
        lang = cls._lang_from_ext(file_type)
        if lang is None:
            return content.strip()

        if lang == "python":
            return cls._strip_python_comments_tokenize(content).strip()
        if lang == "cstyle":
            return cls._strip_cstyle_comments(content).strip()

        spec = cls.LANG_SPECS.get(lang)
        if not spec:
            return content.strip()

        cleaned = content
        for pat in spec.patterns:
            cleaned = pat.sub("", cleaned)
        return cleaned.strip()

    @staticmethod
    def compress(content: str, level: int = 9) -> bytes:
        """Compress code using zlib. Returns bytes."""
        return zlib.compress(content.encode("utf-8"), level)

    @staticmethod
    def decompress(blob: bytes) -> str:
        """Decompress zlib-compressed code back to text."""
        return zlib.decompress(blob).decode("utf-8")
