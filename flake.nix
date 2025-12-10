{
  description = "Analysis-Ready Code (ARC) - recursively scan directories and prepare code for automated analysis.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        python = pkgs.python3;

        # Main ARC package built from pyproject.toml
        arcPkg = pkgs.python3Packages.buildPythonApplication {
          pname = "analysis-ready-code";
          version = "0.1.0";

          src = ./.;

          # We are using pyproject.toml with a PEP 517 backend.
          format = "pyproject";

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          # xclip is not a Python lib, but we can still add it as a runtime
          # dependency so that `xclip` is available in PATH when running ARC
          # inside a Nix environment.
          propagatedBuildInputs = with pkgs; [
            xclip
          ];

          meta = {
            description = "Utility that scans directories and prepares code for AI/computer analysis by stripping comments, filtering files, and optionally compressing content.";
            homepage = "https://github.com/kevinveenbirkenbach/analysis-ready-code";
            license = pkgs.lib.licenses.agpl3Plus;
            platforms = pkgs.lib.platforms.unix;
          };
        };
      in {
        # Default package for `nix build .` and `nix build .#arc`
        packages.arc = arcPkg;
        packages.default = arcPkg;

        # App for `nix run .#arc`
        apps.arc = {
          type = "app";
          program = "${arcPkg}/bin/arc";
        };

        # Default app for `nix run .`
        apps.default = self.apps.${system}.arc;

        # Dev shell for local development
        devShells.default = pkgs.mkShell {
          name = "arc-dev-shell";

          buildInputs = with pkgs; [
            python3
            python3Packages.pip
            python3Packages.setuptools
            python3Packages.wheel
            xclip
          ];

          shellHook = ''
            echo "ARC dev shell ready. Typical usage:"
            echo "  make test"
            echo "  arc . -x"
          '';
        };
      }
    );
}
