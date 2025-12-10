import io
import os
import subprocess
import sys

from .cli import parse_arguments
from .directory_handler import DirectoryHandler
from .tee import Tee

import shutil
import subprocess

def copy_to_clipboard(text: str, quiet: bool = False):
    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True)
        return

    if shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=text, text=True)
        return

    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=text, text=True)
        return

    if not quiet:
        print("Warning: No clipboard tool found (xclip, wl-copy, pbcopy)", file=sys.stderr)

def main() -> None:
    args = parse_arguments()

    # QUIET MODE:
    # - no terminal output
    # - but clipboard buffer still active
    #
    # Normal:
    # - output goes to stdout
    # - optionally tee into buffer

    buffer = None

    if args.clipboard:
        buffer = io.StringIO()

        if args.quiet:
            # quiet + clipboard → only buffer, no stdout
            output_stream = buffer
        else:
            # normal + clipboard → stdout + buffer
            output_stream = Tee(sys.stdout, buffer)
    else:
        # no clipboard
        if args.quiet:
            # quiet without clipboard → suppress ALL output
            class NullWriter:
                def write(self, *_): pass
                def flush(self): pass
            output_stream = NullWriter()
        else:
            output_stream = sys.stdout

    # Process all paths
    for path in args.paths:
        if os.path.isdir(path):
            DirectoryHandler.handle_directory(
                path,
                file_types=args.file_types,
                ignore_file_strings=args.ignore_file_strings,
                ignore_hidden=args.ignore_hidden,
                verbose=args.verbose and not args.quiet,
                no_comments=args.no_comments,
                compress=args.compress,
                path_contains=args.path_contains,
                content_contains=args.content_contains,
                no_gitignore=args.no_gitignore,
                scan_binary_files=args.scan_binary_files,
                output_stream=output_stream,
            )
        elif os.path.isfile(path):
            if DirectoryHandler.should_print_file(
                path,
                file_types=args.file_types,
                ignore_file_strings=args.ignore_file_strings,
                ignore_hidden=args.ignore_hidden,
                path_contains=args.path_contains,
                content_contains=args.content_contains,
                scan_binary_files=args.scan_binary_files,
            ):
                DirectoryHandler.handle_file(
                    path,
                    file_types=args.file_types,
                    ignore_file_strings=args.ignore_file_strings,
                    ignore_hidden=args.ignore_hidden,
                    no_comments=args.no_comments,
                    compress=args.compress,
                    scan_binary_files=args.scan_binary_files,
                    output_stream=output_stream,
                )
        else:
            if not args.quiet:
                print(f"Error: {path} is neither file nor directory.", file=sys.stderr)
            sys.exit(1)

    # Copy to clipboard if enabled
    if buffer is not None:
        text = buffer.getvalue()
        try:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=False)
        except FileNotFoundError:
            if not args.quiet:
                print("Warning: xclip not found.", file=sys.stderr)
