# src/arc/__main__.py

from . import main as _arc_main


def main() -> None:
    """
    Entry point for the `arc` console script and `python -m arc`.

    This keeps all CLI logic in `arc.__init__.py` (main()) and simply
    delegates to it, so both setuptools/entry_points and Nix wrappers
    can reliably import `arc.__main__:main`.
    """
    _arc_main()


if __name__ == "__main__":
    main()
