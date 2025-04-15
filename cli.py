import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scan directories and print/compile file contents."
    )
    parser.add_argument("paths", nargs='+', help="List of files or directories to scan.")
    parser.add_argument("--file-types", nargs='+', default=[], help="Filter by file types (e.g., .txt, .log).")
    parser.add_argument("--ignore-file-strings", nargs='+', default=[], help="Ignore files and folders containing these strings.")
    parser.add_argument("--ignore-hidden", action='store_true', help="Ignore hidden directories and files.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose mode.")
    parser.add_argument("--no-comments", action='store_true', help="Remove comments from the displayed content based on file type.")
    parser.add_argument("--compress", action='store_true', help="Compress code (for supported file types).")
    parser.add_argument("--path-contains", nargs='+', default=[], help="Display files whose paths contain one of these strings.")
    parser.add_argument("--content-contains", nargs='+', default=[], help="Display files containing one of these strings in their content.")
    parser.add_argument("--no-gitignore", action='store_true', help="Do not respect .gitignore files during scan.")
    parser.add_argument("--scan-binary-files", action='store_true', help="Scan binary files as well (by default these are ignored).")
    
    return parser.parse_args()
