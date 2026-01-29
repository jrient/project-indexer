#!/usr/bin/env python3
"""
Project Indexer - Generate hierarchical index for large codebases.

This script scans a project directory and generates a structured index
that allows AI assistants to progressively understand the codebase
without exceeding context limits.

Usage:
    python index_project.py [project_path] [--output DIR] [--update] [--force]

Examples:
    python index_project.py                     # Index current directory
    python index_project.py /path/to/project    # Index specific project
    python index_project.py --update            # Incremental update
    python index_project.py --force             # Force full re-index
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Dict, Tuple

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from parsers import ParserRegistry, TypeScriptParser, PythonParser
from utils import generate_tree, MetaManager, IgnorePatterns

# Configuration
INDEX_DIR_NAME = "project-index"
MAX_CHARS_PER_FILE = 32000  # ~8k tokens

# Register parsers
ParserRegistry.register(TypeScriptParser())
ParserRegistry.register(PythonParser())


def detect_project_type(root_dir: Path) -> tuple[str, list[str]]:
    """
    Detect the project type based on configuration files.

    Returns:
        Tuple of (project_type, tech_stack)
    """
    indicators = {
        "package.json": ("node", ["Node.js"]),
        "tsconfig.json": ("typescript", ["TypeScript"]),
        "pyproject.toml": ("python", ["Python"]),
        "setup.py": ("python", ["Python"]),
        "requirements.txt": ("python", ["Python"]),
        "Cargo.toml": ("rust", ["Rust"]),
        "go.mod": ("go", ["Go"]),
        "pom.xml": ("java", ["Java", "Maven"]),
        "build.gradle": ("java", ["Java", "Gradle"]),
        "composer.json": ("php", ["PHP"]),
        "Gemfile": ("ruby", ["Ruby"]),
    }

    detected_type = "unknown"
    tech_stack = []

    for filename, (proj_type, stack) in indicators.items():
        if (root_dir / filename).exists():
            detected_type = proj_type
            tech_stack.extend(stack)

    # Check for frameworks
    package_json = root_dir / "package.json"
    if package_json.exists():
        try:
            import json
            with open(package_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "react" in deps:
                    tech_stack.append("React")
                if "vue" in deps:
                    tech_stack.append("Vue")
                if "angular" in deps or "@angular/core" in deps:
                    tech_stack.append("Angular")
                if "next" in deps:
                    tech_stack.append("Next.js")
                if "express" in deps:
                    tech_stack.append("Express")
                if "fastify" in deps:
                    tech_stack.append("Fastify")
        except (json.JSONDecodeError, IOError):
            pass

    return detected_type, list(set(tech_stack))


def collect_files(
    root_dir: Path,
    ignore_patterns: IgnorePatterns,
) -> dict[str, list[Path]]:
    """
    Collect all parseable files grouped by directory.

    Returns:
        Dict mapping relative directory paths to lists of file paths
    """
    files_by_dir: dict[str, list[Path]] = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_dir = Path(dirpath)

        # Filter directories in-place
        dirnames[:] = [
            d for d in dirnames
            if not ignore_patterns.should_ignore(current_dir / d)
        ]

        # Get relative directory path
        try:
            rel_dir = current_dir.relative_to(root_dir)
            rel_dir_str = str(rel_dir) if str(rel_dir) != "." else ""
        except ValueError:
            continue

        # Filter and collect files
        for filename in filenames:
            file_path = current_dir / filename

            if ignore_patterns.should_ignore(file_path):
                continue

            parser = ParserRegistry.get_parser(file_path)
            if parser:
                files_by_dir[rel_dir_str].append(file_path)

    return dict(files_by_dir)


def generate_directory_index(
    rel_dir: str,
    files: list[Path],
    root_dir: Path,
) -> str:
    """
    Generate markdown index content for a directory.

    Args:
        rel_dir: Relative directory path
        files: List of files in the directory
        root_dir: Project root directory

    Returns:
        Markdown content for the directory index
    """
    lines = []

    # Header
    dir_name = rel_dir if rel_dir else "Root Directory"
    lines.append(f"# {dir_name}")
    lines.append("")
    lines.append("## Directory Purpose")
    lines.append("_AI can describe the purpose of this directory here_")
    lines.append("")
    lines.append("## Files")
    lines.append("")

    # Process each file
    for file_path in sorted(files, key=lambda p: p.name.lower()):
        rel_path = file_path.relative_to(root_dir)
        parser = ParserRegistry.get_parser(file_path)

        if not parser:
            continue

        lines.append(f"### {file_path.name}")
        lines.append(f"**Path**: `{rel_path}`")
        lines.append(f"**Language**: {parser.language_name}")
        lines.append("")

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            signature = parser.parse(content)
            markdown = parser.format_markdown(signature)
            lines.append(markdown)
        except Exception as e:
            lines.append(f"_Error parsing file: {e}_")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def write_chunked_index(
    content: str,
    output_dir: Path,
    base_name: str,
) -> list[str]:
    """
    Write index content, splitting into chunks if necessary.

    Returns:
        List of written file paths (relative to output_dir parent)
    """
    written_files = []

    if len(content) <= MAX_CHARS_PER_FILE:
        # Single file
        output_path = output_dir / f"{base_name}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        written_files.append(str(output_path.relative_to(output_dir.parent)))
    else:
        # Split into chunks
        chunks = []
        current_chunk = []
        current_size = 0

        for line in content.split("\n"):
            line_size = len(line) + 1
            if current_size + line_size > MAX_CHARS_PER_FILE and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        for i, chunk in enumerate(chunks, 1):
            output_path = output_dir / f"{base_name}_part{i}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if i > 1:
                chunk = f"# {base_name} (Part {i})\n\n" + chunk

            output_path.write_text(chunk, encoding="utf-8")
            written_files.append(str(output_path.relative_to(output_dir.parent)))

    return written_files


def generate_main_index(
    root_dir: Path,
    index_dir: Path,
    project_type: str,
    tech_stack: list[str],
    ignore_patterns: IgnorePatterns,
) -> None:
    """Generate the main INDEX.md file."""
    lines = []

    project_name = root_dir.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# Project Index: {project_name}")
    lines.append("")
    lines.append("## Project Information")
    lines.append(f"- **Type**: {project_type}")
    lines.append(f"- **Tech Stack**: {', '.join(tech_stack) if tech_stack else 'Unknown'}")
    lines.append(f"- **Generated**: {timestamp}")
    lines.append("")
    lines.append("## How to Use This Index")
    lines.append("")
    lines.append("1. Start by reading this main index to understand the project structure")
    lines.append("2. Navigate to specific directory indexes based on your task")
    lines.append("3. Each directory index contains file summaries with exports/definitions")
    lines.append("")
    lines.append("## Directory Structure")
    lines.append("")
    lines.append("```")
    lines.append(generate_tree(root_dir, should_ignore=ignore_patterns.should_ignore, max_depth=4))
    lines.append("```")
    lines.append("")
    lines.append("## Directory Index Navigation")
    lines.append("")

    # List all generated index files
    directories_dir = index_dir / "directories"
    if directories_dir.exists():
        index_files = sorted(directories_dir.glob("*.md"))
        for index_file in index_files:
            rel_path = index_file.relative_to(index_dir)
            name = index_file.stem
            lines.append(f"- [{name}]({rel_path})")

    lines.append("")

    # Write main index
    main_index_path = index_dir / "INDEX.md"
    main_index_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate hierarchical project index for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output", "-o",
        help=f"Output directory name (default: {INDEX_DIR_NAME})",
        default=INDEX_DIR_NAME,
    )
    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="Incremental update (only re-index changed files)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force full re-index",
    )

    args = parser.parse_args()

    # Resolve paths
    root_dir = Path(args.project_path).resolve()
    index_dir = root_dir / args.output
    directories_dir = index_dir / "directories"

    if not root_dir.exists():
        print(f"Error: Project directory not found: {root_dir}")
        sys.exit(1)

    print(f"Indexing project: {root_dir}")

    # Initialize components
    ignore_patterns = IgnorePatterns(root_dir)
    meta_manager = MetaManager(index_dir)

    # Detect project type
    project_type, tech_stack = detect_project_type(root_dir)
    meta_manager.set_project_type(project_type)
    print(f"Detected project type: {project_type}")
    print(f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}")

    # Collect files
    print("Scanning files...")
    files_by_dir = collect_files(root_dir, ignore_patterns)

    total_files = sum(len(files) for files in files_by_dir.values())
    print(f"Found {total_files} indexable files in {len(files_by_dir)} directories")

    # Process directories
    directories_dir.mkdir(parents=True, exist_ok=True)

    for rel_dir, files in files_by_dir.items():
        # Check if update is needed
        if args.update and not args.force:
            needs_update = False
            for file_path in files:
                if meta_manager.should_reindex(str(file_path)):
                    needs_update = True
                    break
            if not needs_update:
                continue

        dir_name = rel_dir if rel_dir else "root"
        print(f"Indexing: {dir_name}")

        # Generate index content
        content = generate_directory_index(rel_dir, files, root_dir)

        # Write index file(s)
        safe_name = rel_dir.replace(os.sep, "_").replace("/", "_") if rel_dir else "root"
        written_files = write_chunked_index(content, directories_dir, safe_name)

        # Update metadata
        for file_path in files:
            for written_file in written_files:
                meta_manager.update_file_record(str(file_path), written_file)

    # Generate main index
    print("Generating main index...")
    generate_main_index(root_dir, index_dir, project_type, tech_stack, ignore_patterns)

    # Save metadata
    meta_manager.save()

    print(f"\nIndex generated at: {index_dir}")
    print(f"Main index: {index_dir / 'INDEX.md'}")


if __name__ == "__main__":
    main()
