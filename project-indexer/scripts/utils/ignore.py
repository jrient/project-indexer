"""
Gitignore-style pattern matching for file filtering.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Optional, Union, List


class IgnorePatterns:
    """
    Handles gitignore-style pattern matching for filtering files and directories.
    """

    # Default patterns to always ignore
    DEFAULT_PATTERNS = [
        ".git",
        ".git/**",
        "node_modules",
        "node_modules/**",
        "__pycache__",
        "__pycache__/**",
        "*.pyc",
        ".pytest_cache",
        ".pytest_cache/**",
        "dist",
        "dist/**",
        "build",
        "build/**",
        "coverage",
        "coverage/**",
        ".next",
        ".next/**",
        ".nuxt",
        ".nuxt/**",
        "venv",
        "venv/**",
        ".venv",
        ".venv/**",
        "env",
        "env/**",
        ".env",
        "*.log",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        "*~",
        ".idea",
        ".idea/**",
        ".vscode",
        ".vscode/**",
        "project-index",
        "project-index/**",
    ]

    def __init__(self, root_dir: str | Path, custom_patterns: Optional[list[str]] = None):
        """
        Initialize with root directory and optional custom patterns.

        Args:
            root_dir: Project root directory
            custom_patterns: Additional patterns to ignore
        """
        self.root_dir = Path(root_dir).resolve()
        self.patterns: list[str] = list(self.DEFAULT_PATTERNS)

        # Load .gitignore if exists
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            self._load_gitignore(gitignore_path)

        # Load .indexignore if exists
        indexignore_path = self.root_dir / ".indexignore"
        if indexignore_path.exists():
            self._load_gitignore(indexignore_path)

        # Add custom patterns
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def _load_gitignore(self, path: Path) -> None:
        """Load patterns from a gitignore-style file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        # Handle negation patterns (not fully supported, just skip)
                        if line.startswith("!"):
                            continue
                        self.patterns.append(line)
        except (IOError, UnicodeDecodeError):
            pass

    def should_ignore(self, path: str | Path) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check (can be absolute or relative)

        Returns:
            True if the path should be ignored
        """
        path = Path(path)

        # Get relative path from root
        try:
            rel_path = path.relative_to(self.root_dir)
        except ValueError:
            # Path is not relative to root, use as-is
            rel_path = path

        # Convert to string with forward slashes for matching
        rel_str = str(rel_path).replace(os.sep, "/")
        name = path.name

        for pattern in self.patterns:
            # Normalize pattern
            pattern = pattern.rstrip("/")

            # Check if pattern matches the full path or just the name
            if "/" in pattern:
                # Pattern contains path separator, match against full relative path
                if fnmatch.fnmatch(rel_str, pattern):
                    return True
                # Also check if it matches with leading slash removed
                if pattern.startswith("/"):
                    if fnmatch.fnmatch(rel_str, pattern[1:]):
                        return True
            else:
                # Pattern is just a name, match against basename
                if fnmatch.fnmatch(name, pattern):
                    return True

            # Check if any parent directory matches
            for parent in rel_path.parents:
                parent_name = parent.name
                if fnmatch.fnmatch(parent_name, pattern):
                    return True

        return False

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """
        Filter a list of paths, removing ignored ones.

        Args:
            paths: List of paths to filter

        Returns:
            Filtered list with ignored paths removed
        """
        return [p for p in paths if not self.should_ignore(p)]
