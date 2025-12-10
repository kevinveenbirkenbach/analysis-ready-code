import fnmatch
import os
import sys

from .code_processor import CodeProcessor


class DirectoryHandler:
    @staticmethod
    def load_gitignore_patterns(root_path):
        """
        Recursively scans for .gitignore files in the given root_path.
        Returns a list of tuples (base_dir, patterns) where:
          - base_dir: the directory in which the .gitignore was found.
          - patterns: a list of pattern strings from that .gitignore.
        """
        gitignore_data = []
        for dirpath, _, filenames in os.walk(root_path):
            if ".gitignore" in filenames:
                gitignore_path = os.path.join(dirpath, ".gitignore")
                try:
                    with open(gitignore_path, "r") as f:
                        lines = f.readlines()
                    # Filter out empty lines and comments.
                    patterns = [
                        line.strip()
                        for line in lines
                        if line.strip() and not line.strip().startswith("#")
                    ]
                    # Save the base directory and its patterns.
                    gitignore_data.append((dirpath, patterns))
                except Exception as e:  # pragma: no cover - defensive
                    print(f"Error reading {gitignore_path}: {e}", file=sys.stderr)
        return gitignore_data

    @staticmethod
    def is_binary_file(file_path):
        """
        Reads the first 1024 bytes of file_path and heuristically determines
        if the file appears to be binary. This method returns True if a null byte
        is found or if more than 30% of the bytes in the sample are non-text.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
            # If there's a null byte, it's almost certainly binary.
            if b"\x00" in chunk:
                return True

            # Define a set of text characters (ASCII printable + common control characters)
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x7F)))
            # Count non-text characters in the chunk.
            non_text = sum(byte not in text_chars for byte in chunk)
            if len(chunk) > 0 and (non_text / len(chunk)) > 0.30:
                return True
        except Exception:  # pragma: no cover - defensive
            # If the file cannot be read in binary mode, assume it's not binary.
            return False
        return False

    @staticmethod
    def is_gitignored(file_path, gitignore_data):
        """
        Checks if file_path should be ignored according to the .gitignore entries.
        For each tuple (base_dir, patterns), if file_path is under base_dir,
        computes the relative path and matches it against the patterns.
        """
        for base_dir, patterns in gitignore_data:
            try:
                rel_path = os.path.relpath(file_path, base_dir)
            except ValueError:
                # file_path and base_dir are on different drives.
                continue
            # If the file is not under the current .gitignore base_dir, skip it.
            if rel_path.startswith(".."):
                continue
            # Check all patterns.
            for pattern in patterns:
                if pattern.endswith("/"):
                    # Directory pattern: check if any folder in the relative path matches.
                    parts = rel_path.split(os.sep)
                    for part in parts[:-1]:
                        if fnmatch.fnmatch(part + "/", pattern):
                            return True
                else:
                    # Check if the relative path matches the pattern.
                    if fnmatch.fnmatch(rel_path, pattern):
                        return True
        return False

    @staticmethod
    def filter_directories(dirs, ignore_file_strings, ignore_hidden):
        """
        Filter out directories based on ignore_file_strings and hidden status.
        """
        if ignore_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        dirs[:] = [d for d in dirs if not any(ig in d for ig in ignore_file_strings)]

    @staticmethod
    def path_or_content_contains(file_path, path_contains, content_contains):
        """
        Check if the file path contains specific strings or if the file content does.
        """
        if path_contains and any(whitelist_str in file_path for whitelist_str in path_contains):
            return True

        if content_contains:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                if any(whitelist_str in content for whitelist_str in content_contains):
                    return True
            except UnicodeDecodeError:
                return False
        return False

    @staticmethod
    def should_print_file(
        file_path,
        file_types,
        ignore_file_strings,
        ignore_hidden,
        path_contains,
        content_contains,
        scan_binary_files=False,
    ):
        """
        Determines if a file should be printed based on various criteria.
        By default, binary files are skipped unless scan_binary_files is True.
        """
        # Check binary file status using our heuristic.
        if not scan_binary_files and DirectoryHandler.is_binary_file(file_path):
            return False

        if ignore_hidden and os.path.basename(file_path).startswith("."):
            return False

        if file_types and not any(file_path.endswith(ft) for ft in file_types):
            return False

        if any(ignore_str in file_path for ignore_str in ignore_file_strings):
            return False

        if path_contains or content_contains:
            return DirectoryHandler.path_or_content_contains(
                file_path, path_contains, content_contains
            )
        return True

    @staticmethod
    def print_file_content(file_path, no_comments, compress, output_stream):
        """
        Prints the content of a file, optionally removing comments or compressing the output.
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
            if no_comments:
                file_type = os.path.splitext(file_path)[1]
                content = CodeProcessor.remove_comments(content, file_type)
            print(f"<< START: {file_path} >>", file=output_stream)
            if compress:
                compressed_content = CodeProcessor.compress(content)
                print("COMPRESSED CODE:", file=output_stream)
                print(compressed_content, file=output_stream)
            else:
                print(content, file=output_stream)
            print("<< END >>\n", file=output_stream)
        except UnicodeDecodeError:
            print(
                f"Warning: Could not read file due to encoding issues: {file_path}",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def handle_directory(directory, **kwargs):
        """
        Scans the directory and processes each file while respecting .gitignore rules.
        """
        gitignore_data = []
        if not kwargs.get("no_gitignore"):
            gitignore_data = DirectoryHandler.load_gitignore_patterns(directory)

        output_stream = kwargs.get("output_stream", sys.stdout)

        for root, dirs, files in os.walk(directory):
            DirectoryHandler.filter_directories(
                dirs, kwargs["ignore_file_strings"], kwargs["ignore_hidden"]
            )
            for file in files:
                file_path = os.path.join(root, file)
                if gitignore_data and DirectoryHandler.is_gitignored(file_path, gitignore_data):
                    if kwargs.get("verbose"):
                        print(f"Skipped (gitignored): {file_path}", file=output_stream)
                    continue

                if DirectoryHandler.should_print_file(
                    file_path,
                    kwargs["file_types"],
                    kwargs["ignore_file_strings"],
                    kwargs["ignore_hidden"],
                    kwargs["path_contains"],
                    kwargs["content_contains"],
                    scan_binary_files=kwargs.get("scan_binary_files", False),
                ):
                    DirectoryHandler.print_file_content(
                        file_path,
                        kwargs["no_comments"],
                        kwargs["compress"],
                        output_stream=output_stream,
                    )
                elif kwargs.get("verbose"):
                    print(f"Skipped file: {file_path}", file=output_stream)

    @staticmethod
    def handle_file(file_path, **kwargs):
        """
        Processes an individual file.
        """
        output_stream = kwargs.get("output_stream", sys.stdout)
        DirectoryHandler.print_file_content(
            file_path,
            kwargs["no_comments"],
            kwargs["compress"],
            output_stream=output_stream,
        )
