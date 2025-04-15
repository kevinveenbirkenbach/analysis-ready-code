import os
import fnmatch
from code_processor import CodeProcessor

class DirectoryHandler:
    @staticmethod
    def load_gitignore_patterns(root_path):
        """Collect .gitignore patterns from root_path and all subdirectories."""
        gitignore_patterns = []
        for dirpath, dirnames, filenames in os.walk(root_path):
            if '.gitignore' in filenames:
                gitignore_path = os.path.join(dirpath, '.gitignore')
                try:
                    with open(gitignore_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Erzeuge einen absoluten Pattern-Pfad basierend auf dem Speicherort der .gitignore
                                gitignore_patterns.append(os.path.join(dirpath, line))
                except Exception as e:
                    print(f"Error reading {gitignore_path}: {e}")
        return gitignore_patterns

    @staticmethod
    def is_gitignored(file_path, gitignore_patterns):
        """Check if file_path matches any .gitignore pattern."""
        for pattern in gitignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    @staticmethod
    def filter_directories(dirs, ignore_file_strings, ignore_hidden):
        """Filter out directories based on ignore criteria."""
        if ignore_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        dirs[:] = [d for d in dirs if not any(ig in d for ig in ignore_file_strings)]

    @staticmethod
    def path_or_content_contains(file_path, path_contains, content_contains):
        # Check if the file path contains specific strings (whitelist)
        if path_contains and any(whitelist_str in file_path for whitelist_str in path_contains):
            return True

        # Check file content for specific strings (if specified)
        if content_contains:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                if any(whitelist_str in content for whitelist_str in content_contains):
                    return True
            except UnicodeDecodeError:
                return False
        return False

    @staticmethod
    def should_print_file(file_path, file_types, ignore_file_strings, ignore_hidden, path_contains, content_contains):
        """
        Determine if a file should be printed based on various criteria.
        """
        if ignore_hidden and os.path.basename(file_path).startswith('.'):
            return False

        if file_types and not any(file_path.endswith(file_type) for file_type in file_types):
            return False

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
                print("COMPRESSED CODE: ")
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
        gitignore_patterns = []
        if not kwargs.get('no_gitignore'):
            gitignore_patterns = DirectoryHandler.load_gitignore_patterns(directory)

        for root, dirs, files in os.walk(directory):
            DirectoryHandler.filter_directories(dirs, kwargs['ignore_file_strings'], kwargs['ignore_hidden'])
            for file in files:
                file_path = os.path.join(root, file)
                if gitignore_patterns and DirectoryHandler.is_gitignored(file_path, gitignore_patterns):
                    if kwargs.get('verbose'):
                        print(f"Skipped (gitignored): {file_path}")
                    continue

                if DirectoryHandler.should_print_file(
                    file_path,
                    kwargs['file_types'],
                    kwargs['ignore_file_strings'],
                    kwargs['ignore_hidden'],
                    kwargs['path_contains'],
                    kwargs['content_contains']
                ):
                    DirectoryHandler.print_file_content(file_path, kwargs['no_comments'], kwargs['compress'])
                elif kwargs.get('verbose'):
                    print(f"Skipped file: {file_path}")

    @staticmethod
    def handle_file(file_path, **kwargs):
        """Handle scanning and printing for individual files."""
        DirectoryHandler.print_file_content(file_path, kwargs['no_comments'], kwargs['compress'])
