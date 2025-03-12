# 🤖👩‍🔬 Analysis-Ready Code (ARC)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach) [![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach) [![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)


Analysis-Ready Code (ARC) is a Python-based utility designed to recursively scan directories and transform source code into a format optimized for AI and computer analysis. By stripping comments, filtering specific file types, and optionally compressing content, ARC ensures that your code is clean and ready for automated processing.

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.x
- [Kevin's Package Manager](https://github.com/kevinveenbirkenbach/package-manager) installed

### 🛠️ Installation via Package Manager

ARC is available through the package manager under the alias `arc`. To install it, follow these steps:

1. Ensure that you have Kevin's Package Manager set up on your system. Follow the instructions on [the package manager repository](https://github.com/kevinveenbirkenbach/package-manager) if you haven't done so already.
2. Install ARC using the package manager:
   ```bash
   package-manager install arc
   ```
   This command will download and install ARC and make it available globally via the alias `arc`.

### ⚡ Running ARC

Once installed, you can run ARC directly from the terminal using its alias:

```bash
arc /path/to/directory [options]
```

## 📖 Usage

ARC scans the specified directories and processes source code to prepare it for automated analysis. It can filter by file type, remove comments, and compress the content for efficient processing.

To view the help page and all available options, execute:

```bash
arc --help
```

### Options:

- **paths**: List of files or directories to scan. This is a positional argument.
- **--file-types**: Filter by file types (e.g., `.py`, `.js`, `.c`). Only files with these extensions will be processed.
- **--ignore-file-strings**: Ignore files and folders containing these strings. Useful for excluding specific files or directories.
- **--ignore-hidden**: Ignore hidden directories and files (those starting with a dot).
- **-v, --verbose**: Enable verbose mode to print additional information about skipped files.
- **--no-comments**: Remove comments from the displayed content based on file type. This is especially useful for preparing code for automated analysis.
- **--compress**: Compress code (for supported file types) to further optimize it for analysis.
- **--path-contains**: Display files whose paths contain one of these strings. Useful for narrowing down the scan to specific parts of the directory structure.
- **--content-contains**: Display files containing one of these strings in their content.

## ⚠️ Caution

ARC is designed to prepare code for analysis by removing extraneous elements like comments. Exercise caution when scanning directories with large files, as the script may produce extensive output. Always assess the data volume before executing the script.

## 🤝 Contributing

Contributions via pull requests are welcome. For significant modifications, kindly open an issue first to discuss the proposed changes.

## ✍️ Author

**Kevin Veen-Birkenbach**  
- 📧 [Email Kevin](mailto:kevin@veen.world)
- 🌐 [Website](https://www.veen.world/)

## 📜 License

This project is licensed under the GNU Affero General Public License v3.0. The complete license text is available in the `LICENSE` file.

## 🙏 Acknowledgements

Special thanks to the community and tools like OpenAI's ChatGPT for assisting in the development process.
