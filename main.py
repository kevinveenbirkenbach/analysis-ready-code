#!/usr/bin/env python3
import os
import sys
from cli import parse_arguments
from directory_handler import DirectoryHandler

def main():
    args = parse_arguments()
    
    for path in args.paths:
        if os.path.isdir(path):
            DirectoryHandler.handle_directory(
                path,
                file_types=args.file_types,
                ignore_file_strings=args.ignore_file_strings,
                ignore_hidden=args.ignore_hidden,
                verbose=args.verbose,
                no_comments=args.no_comments,
                compress=args.compress,
                path_contains=args.path_contains,
                content_contains=args.content_contains,
                no_gitignore=args.no_gitignore,
                scan_binary_files=args.scan_binary_files
            )
        elif os.path.isfile(path):
            if DirectoryHandler.should_print_file(
                path,
                file_types=args.file_types,
                ignore_file_strings=args.ignore_file_strings,
                ignore_hidden=args.ignore_hidden,
                path_contains=args.path_contains,
                content_contains=args.content_contains,
                scan_binary_files=args.scan_binary_files
            ):
                DirectoryHandler.handle_file(
                    path,
                    file_types=args.file_types,
                    ignore_file_strings=args.ignore_file_strings,
                    ignore_hidden=args.ignore_hidden,
                    no_comments=args.no_comments,
                    compress=args.compress,
                    scan_binary_files=args.scan_binary_files
                )
        else:
            print(f"Error: {path} is neither a valid file nor a directory.")
            sys.exit(1)

if __name__ == "__main__":
    main()
