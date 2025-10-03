# Makefile for ARC
.PHONY: test install help

help:
	@echo "Targets:"
	@echo "  make test     - Run unit tests"
	@echo "  make install  - Show how to install via Kevin's Package Manager"

test:
	@python -m unittest discover -s tests -p "test_*.py" -t .

install:
	@echo "ARC is distributed via Kevin's Package Manager."
	@echo "Install it with:"
	@echo "    package-manager install arc"
	@echo ""
	@echo "(This 'make install' does not perform any other actions.)"
