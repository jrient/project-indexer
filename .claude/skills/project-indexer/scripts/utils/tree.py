"""
Directory tree generator for project visualization.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Union


def generate_tree(
    root_dir: str | Path,
    should_ignore: Optional[Callable[[Path], bool]] = None,
    max_depth: int = 10,
    show_files: bool = True,
    max_files_per_dir: int = 20,
) -> str:
    """
    Generate a directory tree structure as a string.

    Args:
        root_dir: Root directory to start from
        should_ignore: Optional callback to check if path should be ignored
        max_depth: Maximum depth to traverse
        show_files: Whether to show files (not just directories)
        max_files_per_dir: Maximum files to show per directory before truncating

    Returns:
        Tree structure as formatted string
    """
    root_dir = Path(root_dir).resolve()
    output_lines = [root_dir.name]

    def _format_tree(directory: Path, prefix: str = "", depth: int = 0) -> None:
        if depth >= max_depth:
            output_lines.append(f"{prefix}└── ...")
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            output_lines.append(f"{prefix}└── [Permission Denied]")
            return

        # Filter ignored entries
        if should_ignore:
            entries = [e for e in entries if not should_ignore(e)]

        # Separate directories and files
        dirs = [e for e in entries if e.is_dir()]
        files = [e for e in entries if e.is_file()] if show_files else []

        # Limit files shown
        files_truncated = len(files) > max_files_per_dir
        if files_truncated:
            files = files[:max_files_per_dir]

        all_entries = dirs + files
        total = len(all_entries) + (1 if files_truncated else 0)

        for i, entry in enumerate(all_entries):
            is_last = i == total - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                output_lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                _format_tree(entry, prefix + extension, depth + 1)
            else:
                output_lines.append(f"{prefix}{connector}{entry.name}")

        if files_truncated:
            remaining = len([e for e in entries if e.is_file()]) - max_files_per_dir
            connector = "└── "
            output_lines.append(f"{prefix}{connector}... ({remaining} more files)")

    _format_tree(root_dir)
    return "\n".join(output_lines)


def generate_compact_tree(
    root_dir: str | Path,
    should_ignore: Optional[Callable[[Path], bool]] = None,
    max_depth: int = 3,
) -> str:
    """
    Generate a compact tree showing only directories and key files.

    Args:
        root_dir: Root directory to start from
        should_ignore: Optional callback to check if path should be ignored
        max_depth: Maximum depth to traverse

    Returns:
        Compact tree structure as formatted string
    """
    key_files = {
        "package.json",
        "tsconfig.json",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "Makefile",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        ".env.example",
    }

    def is_key_file(path: Path) -> bool:
        return path.name in key_files or path.suffix in {".md"} and path.name.startswith("README")

    root_dir = Path(root_dir).resolve()
    output_lines = [root_dir.name]

    def _format_tree(directory: Path, prefix: str = "", depth: int = 0) -> None:
        if depth >= max_depth:
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        if should_ignore:
            entries = [e for e in entries if not should_ignore(e)]

        dirs = [e for e in entries if e.is_dir()]
        files = [e for e in entries if e.is_file() and is_key_file(e)]

        all_entries = dirs + files
        total = len(all_entries)

        for i, entry in enumerate(all_entries):
            is_last = i == total - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                output_lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                _format_tree(entry, prefix + extension, depth + 1)
            else:
                output_lines.append(f"{prefix}{connector}{entry.name}")

    _format_tree(root_dir)
    return "\n".join(output_lines)
