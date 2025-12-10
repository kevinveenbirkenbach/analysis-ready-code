# Makefile for ARC
SHELL := /usr/bin/env bash

APP_NAME := arc
BIN_DIR ?= $(HOME)/.local/bin
# Flake attribute for the ARC app
NIX_ATTR := .#arc

.PHONY: help test install uninstall detect-nix \
        install-with-nix install-with-python install-nix install-python \
        uninstall-nix-wrapper uninstall-python

help:
	@echo "Targets:"
	@echo "  make test               - Run unit tests"
	@echo "  make install            - Install ARC using Nix if available (and usable),"
	@echo "                            otherwise fall back to Python."
	@echo "  make uninstall          - Uninstall ARC (Nix wrapper + Python package)"
	@echo "  make install-nix        - Force Nix installation (no fallback)"
	@echo "  make install-python     - Force Python installation"
	@echo "  make uninstall-nix-wrapper - Remove only the arc binary/symlink from BIN_DIR"
	@echo "  make uninstall-python   - Remove the Python package 'arc'"

test:
	@python -m unittest discover -s tests -p "test_*.py" -t .

# -------------------------------------------------------------------
# Smart installation selector
# -------------------------------------------------------------------
install: detect-nix

detect-nix:
	@if command -v nix >/dev/null 2>&1; then \
		echo "Nix detected → trying Nix-based installation…"; \
		if $(MAKE) install-with-nix; then \
			echo "Nix installation succeeded."; \
		else \
			echo "Nix installation failed → falling back to Python…"; \
			$(MAKE) install-with-python; \
		fi; \
	else \
		echo "Nix NOT found → installing via Python…"; \
		$(MAKE) install-with-python; \
	fi

# Convenience aliases, if you want to force one path:
install-nix:
	$(MAKE) install-with-nix

install-python:
	$(MAKE) install-with-python

# -------------------------------------------------------------------
# Nix installation (flakes + nix-command enabled via flags)
# -------------------------------------------------------------------
install-with-nix:
	@echo "Building ARC using Nix ($(NIX_ATTR))..."
	nix --extra-experimental-features 'nix-command flakes' build $(NIX_ATTR)
	@echo "Installing into $(BIN_DIR)..."
	mkdir -p "$(BIN_DIR)"
	ln -sf "$(PWD)/result/bin/$(APP_NAME)" "$(BIN_DIR)/$(APP_NAME)"
	@echo "Done (Nix). Run: $(APP_NAME) --help"

# -------------------------------------------------------------------
# Python installation (fallback if Nix is unavailable or unusable)
# - In a virtualenv: install into the venv (no --user).
# - Outside a virtualenv: install with --user.
# -------------------------------------------------------------------
install-with-python:
	@echo "Installing ARC via Python…"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Virtualenv detected at $$VIRTUAL_ENV → installing into venv (no --user)…"; \
		python -m pip install --upgrade .; \
	else \
		echo "No virtualenv detected → installing with --user…"; \
		python -m pip install --user --upgrade .; \
	fi
	@echo "Ensuring $(BIN_DIR) exists..."
	mkdir -p "$(BIN_DIR)"
	@echo "Checking for arc binary in $(BIN_DIR)…"
	@if [ ! -f "$(BIN_DIR)/$(APP_NAME)" ] && [ ! -L "$(BIN_DIR)/$(APP_NAME)" ]; then \
		echo "arc executable not found in $(BIN_DIR), creating wrapper…"; \
		echo '#!/usr/bin/env bash' > "$(BIN_DIR)/$(APP_NAME)"; \
		echo 'python -m arc "$$@"' >> "$(BIN_DIR)/$(APP_NAME)"; \
		chmod +x "$(BIN_DIR)/$(APP_NAME)"; \
	else \
		echo "arc already present in $(BIN_DIR), not touching it."; \
	fi
	@echo "Done (Python). Make sure $(BIN_DIR) is in your PATH."

# -------------------------------------------------------------------
# High-level uninstall target (calls Nix + Python uninstall helpers)
# -------------------------------------------------------------------
uninstall: uninstall-nix-wrapper uninstall-python
	@echo "=== Uninstall finished ==="

# -------------------------------------------------------------------
# Nix side: remove wrapper/binary from BIN_DIR
# -------------------------------------------------------------------
uninstall-nix-wrapper:
	@echo "Removing '$(APP_NAME)' from $(BIN_DIR)..."
	@if [ -L "$(BIN_DIR)/$(APP_NAME)" ] || [ -f "$(BIN_DIR)/$(APP_NAME)" ]; then \
		rm -f "$(BIN_DIR)/$(APP_NAME)"; \
		echo "✔ Removed $(BIN_DIR)/$(APP_NAME)"; \
	else \
		echo "⚠ No '$(APP_NAME)' binary found in $(BIN_DIR)."; \
	fi

# -------------------------------------------------------------------
# Python side: uninstall the arc package
# - In a virtualenv: uninstall from venv.
# - Outside a virtualenv: uninstall from user/system environment.
# -------------------------------------------------------------------
uninstall-python:
	@echo "Checking for Python installation of 'arc'…"
	@if python -c "import arc" >/dev/null 2>&1; then \
		echo "Python package 'arc' detected → uninstalling…"; \
		if [ -n "$$VIRTUAL_ENV" ]; then \
			echo "Virtualenv detected ($$VIRTUAL_ENV) → uninstalling inside venv…"; \
			python -m pip uninstall -y arc; \
		else \
			echo "No virtualenv detected → uninstalling from user/system environment…"; \
			python -m pip uninstall -y arc; \
		fi; \
		echo "✔ Python uninstall complete."; \
	else \
		echo "⚠ Python module 'arc' not installed. Skipping Python uninstall."; \
	fi
