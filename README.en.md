English | [简体中文](./README.md)

# Project Indexer

Generate a hierarchical index for large codebases, enabling AI assistants to understand your project structure progressively without exceeding context limits.

## Why?

When a project grows large, AI assistants struggle to understand the entire codebase at once. Project Indexer pre-builds a "cognitive map" of your project, allowing you to:

- **Get oriented fast** - Grasp the structure and architecture of a large project at first glance
- **Find code precisely** - Locate where a specific feature is implemented
- **Iterate efficiently** - Quickly identify the files that need changes during development
- **Break the limits** - Solve the problem of projects being too large for an AI to understand in a single pass

## Features

- **Multi-language support** - Supports TypeScript/JavaScript and Python
- **Incremental updates** - Only re-indexes changed files, saving time
- **Smart ignoring** - Automatically respects `.gitignore` and `.indexignore` rules
- **Project detection** - Automatically identifies project type and tech stack
- **Symbol extraction** - Precisely extracts definitions of classes, functions, interfaces, types, and more
- **Extensible architecture** - Easy to add support for new languages

## Quick Start

### Basic Usage

```bash
# Index the current directory
python project-indexer/scripts/index_project.py

# Index a specific project
python project-indexer/scripts/index_project.py /path/to/your/project

# Incremental update (only process changed files)
python project-indexer/scripts/index_project.py --update

# Force a full rebuild
python project-indexer/scripts/index_project.py --force
```

### Output Structure

After running, a `project-index/` directory is generated at the project root:

```
project-index/
├── INDEX.md              # Master index (project overview)
├── .index-meta.json      # Incremental update metadata
└── directories/          # Detailed per-directory indexes
    ├── root.md
    ├── src.md
    └── ...
```

## Supported Languages

| Language | Extensions | Extracted Content |
|------|--------|----------|
| TypeScript/JavaScript | `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` | Exported functions, classes, interfaces, types, constants |
| Python | `.py`, `.pyi` | Class definitions, function definitions (including methods) |

## Project Structure

```
project-index/
├── project-indexer/              # Source code
│   ├── scripts/
│   │   ├── index_project.py      # Main entry script
│   │   ├── parsers/              # Language parsers
│   │   │   ├── base.py           # Abstract base parser class
│   │   │   ├── python_parser.py  # Python parser
│   │   │   └── typescript.py     # TypeScript parser
│   │   └── utils/                # Utilities
│   │       ├── tree.py           # Directory tree generation
│   │       ├── ignore.py         # Ignore rule handling
│   │       └── meta.py           # Incremental update management
│   ├── references/
│   │   └── supported-languages.md
│   └── SKILL.md                  # Skill documentation
├── project-index/                # Generated index output
└── project-indexer.skill         # Claude Code Skill package
```

## Configuration

### Ignore Rules

Create an `.indexignore` file to customize ignore rules (same syntax as `.gitignore`):

```gitignore
# Ignore test files
**/*.test.ts
**/*.spec.js

# Ignore specific directories
docs/
examples/
```

**Directories ignored by default:**
- `.git`, `node_modules`, `__pycache__`
- `dist`, `build`, `.next`, `.nuxt`
- `venv`, `.venv`, `env`
- And all `project-index` output directories

## Using as a Claude Code Skill

Project Indexer can be used as a Claude Code Skill:

```bash
# Install the skill
claude install project-indexer.skill

# Use it inside Claude Code
/project-indexer
```

## Adding a New Language

Implement the `BaseParser` interface to add support for a new language:

```python
from parsers.base import BaseParser, FileSignature, ParserRegistry

@ParserRegistry.register
class MyLanguageParser(BaseParser):
    @property
    def extensions(self) -> list[str]:
        return [".mylang"]

    @property
    def language_name(self) -> str:
        return "MyLanguage"

    def parse(self, file_path: Path) -> FileSignature:
        # Implement parsing logic here
        return FileSignature(exports=[], imports=[])
```

## Implementation Details

- **Pure Python** - No external dependencies
- **Regex-based parsing** - Fast extraction of code symbols
- **Incremental update mechanism** - Detects changes based on file mtime and size
- **Context limit** - Max 32,000 characters per file (about 8k tokens)

## License

MIT
