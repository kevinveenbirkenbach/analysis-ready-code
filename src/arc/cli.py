import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scan directories and print/compile file contents."
    )

    # Positional: paths
    parser.add_argument(
        "paths",
        nargs="+",
        help="List of files or directories to scan.",
    )

    # File type filter
    parser.add_argument(
        "-t",
        "--file-types",
        nargs="+",
        default=[],
        help="Filter by file types (e.g., .py, .js, .c).",
    )

    # Ignore file/path strings (was previously -x, jetzt -I)
    parser.add_argument(
        "-I",
        "--ignore-file-strings",
        nargs="+",
        default=[],
        help="Ignore files and folders containing these strings.",
    )

    # Clipboard: alias -x
    parser.add_argument(
        "-x",
        "--clipboard",
        action="store_true",
        help="Copy the output to the X clipboard via xclip (alias: -x).",
    )

    # Quiet mode
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress terminal output (useful with --clipboard).",
    )

    # Show hidden files
    parser.add_argument(
        "-S",
        "--show-hidden",
        action="store_true",
        dest="show_hidden",
        default=False,
        help="Include hidden directories and files.",
    )

    # Verbose
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose mode.",
    )

    # Strip comments
    parser.add_argument(
        "-N",
        "--no-comments",
        action="store_true",
        help="Remove comments from files before printing.",
    )

    # Compress
    parser.add_argument(
        "-z",
        "--compress",
        action="store_true",
        help="Compress content instead of printing plain text.",
    )

    # Path filter
    parser.add_argument(
        "-p",
        "--path-contains",
        nargs="+",
        default=[],
        help="Only include files whose *path* contains one of these strings.",
    )

    # Content filter
    parser.add_argument(
        "-C",
        "--content-contains",
        nargs="+",
        default=[],
        help="Only include files whose *content* contains one of these strings.",
    )

    # Ignore .gitignore
    parser.add_argument(
        "-G",
        "--no-gitignore",
        action="store_true",
        help="Do not respect .gitignore files during scan.",
    )

    # Scan binary files
    parser.add_argument(
        "-b",
        "--scan-binary-files",
        action="store_true",
        help="Also scan binary files (ignored by default).",
    )

    args = parser.parse_args()
    args.ignore_hidden = not args.show_hidden
    return args
