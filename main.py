#!/usr/bin/env python3

import os
import argparse
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
                (r'\s*#.*', '',0),
                (r'\"\"\"(.*?)\"\"\"', '', re.DOTALL),
                (r"\'\'\'(.*?)\'\'\'", '', re.DOTALL)
            ],
            CodeProcessor.JS: [
                (r'\s*//.*', '',0),
                (r'/\*.*?\*/', '',0)
            ],
            CodeProcessor.C: [
                (r'\s*//.*', '',0),
                (r'/\*.*?\*/', '',0)
            ],
            CodeProcessor.CPP: [
                (r'\s*//.*', '',0),
                (r'/\*.*?\*/', '',0)
            ],
            CodeProcessor.H: [
                (r'\s*//.*', '',0),
                (r'/\*.*?\*/', '',0)
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


class DirectoryHandler:
    
    @staticmethod
    def filter_directories(dirs, ignore_file_strings, ignore_hidden):
        """Filter out directories based on ignore criteria."""
        if ignore_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        dirs[:] = [d for d in dirs if not any(ig in d for ig in ignore_file_strings)]

    @staticmethod
    def path_or_content_contains(file_path, path_contains, content_contains):
        # Check if the file name contains specific strings (whitelist)
        if path_contains and any(whitelist_str in file_path for whitelist_str in path_contains):
            return True

        # Check file content for specific strings (if specified)
        if content_contains:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                # Return True if any of the content_contains strings are found in the content
                if any(whitelist_str in content for whitelist_str in content_contains):
                    return True
            except UnicodeDecodeError:
                # Return False if there's a Unicode decode error (file can't be read)
                return False
        return False

    @staticmethod
    def should_print_file(file_path, file_types, ignore_file_strings, ignore_hidden, path_contains, content_contains):
        """
        Determine if a file should be printed based on various criteria.

        Args:
        file_path (str): The path of the file to be checked.
        file_types (list): List of allowed file extensions.
        ignore_file_strings (list): List of strings; if any are found in the file path, the file is ignored.
        ignore_hidden (bool): If True, hidden files (starting with '.') are ignored.
        path_contains (list): List of strings; the file is processed only if its path contains one of these strings.
        content_contains (list): List of strings; the file is processed only if its content contains one of these strings.

        Returns:
        bool: True if the file should be printed, False otherwise.
        """

        # Check for hidden files if ignore_hidden is enabled
        if ignore_hidden and os.path.basename(file_path).startswith('.'):
            return False

        # Check if the file type is in the allowed list (if specified)
        if file_types and not any(file_path.endswith(file_type) for file_type in file_types):
            return False

        # Check if the file should be ignored based on the presence of specific strings in its path
        if any(ignore_str in file_path for ignore_str in ignore_file_strings):
            return False

        if path_contains or content_contains:
            return DirectoryHandler.path_or_content_contains(file_path, path_contains, content_contains)
        return True
    
    @staticmethod
    def print_file_content(file_path, no_comments, compress):
        """Print the content of a file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            if no_comments:
                file_type = os.path.splitext(file_path)[1]
                content = CodeProcessor.remove_comments(content, file_type)
            print(f"<< START: {file_path} >>")
            if compress:
                compressed_content = CodeProcessor.compress(content)
                print(f"COMPRESSED CODE: ")
                print(compressed_content)
            else:
                print(content)
            print("<< END >>\n")
        except UnicodeDecodeError:
            print(f"Warning: Could not read file due to encoding issues: {file_path}")
            exit(1)

    @staticmethod
    def handle_directory(directory, **kwargs):
        """Handle scanning and printing for directories."""
        for root, dirs, files in os.walk(directory):
            DirectoryHandler.filter_directories(dirs, kwargs['ignore_file_strings'], kwargs['ignore_hidden'])
            for file in files:
                if DirectoryHandler.should_print_file(os.path.join(root, file), kwargs['file_types'], kwargs['ignore_file_strings'], kwargs['ignore_hidden'], kwargs['path_contains'], kwargs['content_contains']):
                    DirectoryHandler.print_file_content(os.path.join(root, file), kwargs['no_comments'], kwargs['compress'])
                elif kwargs['verbose']:
                    print(f"Skipped file: {file}")

    @staticmethod
    def handle_file(file_path, **kwargs):
        """Handle scanning and printing for individual files."""
        DirectoryHandler.print_file_content(file_path, kwargs['no_comments'], kwargs['compress'])


def main():
    parser = argparse.ArgumentParser(description="Scan directories and print/compile file contents.")
    parser.add_argument("paths", nargs='+', help="List of files or directories to scan.")
    parser.add_argument("--file-types", nargs='+', default=[], help="Filter by file types (e.g., .txt .log).")
    parser.add_argument("--ignore-file-strings", nargs='+', default=[], help="Ignore files and folders containing these strings.")
    parser.add_argument("--ignore-hidden", action='store_true', help="Ignore hidden directories and files.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose mode.")
    parser.add_argument("--no-comments", action='store_true', help="Remove comments from the displayed content based on file type.")
    parser.add_argument("--compress", action='store_true', help="Compress code (for Python files).")
    parser.add_argument("--path-contains", nargs='+', default=[], help="Display files whose paths contain one of these strings.")
    parser.add_argument("--content-contains", nargs='+', default=[], help="Display files containing one of these strings in their content.")
    
    args = parser.parse_args()
    
    for path in args.paths:
        if os.path.isdir(path):
            DirectoryHandler.handle_directory(path, file_types=args.file_types, ignore_file_strings=args.ignore_file_strings, ignore_hidden=args.ignore_hidden, verbose=args.verbose, no_comments=args.no_comments, compress=args.compress, path_contains=args.path_contains, content_contains=args.content_contains)
        elif os.path.isfile(path):
            if DirectoryHandler.should_print_file(path, file_types=args.file_types, ignore_file_strings=args.ignore_file_strings, ignore_hidden=args.ignore_hidden, path_contains=args.path_contains, content_contains=args.content_contains):
                DirectoryHandler.handle_file(path, file_types=args.file_types, ignore_file_strings=args.ignore_file_strings, ignore_hidden=args.ignore_hidden, no_comments=args.no_comments, compress=args.compress)
        else:
            print(f"Error: {path} is neither a valid file nor a directory.")
            exit(1)

if __name__ == "__main__":
    main()