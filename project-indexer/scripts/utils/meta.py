"""
Metadata management for incremental indexing.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Set, Dict


@dataclass
class FileRecord:
    """Record of a single indexed file."""
    mtime: float
    size: int
    indexed_in: str
    checksum: Optional[str] = None


@dataclass
class IndexMetadata:
    """Metadata for the entire project index."""
    version: str = "1.0"
    project_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    files: dict[str, dict] = None

    def __post_init__(self):
        if self.files is None:
            self.files = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class MetaManager:
    """
    Manages index metadata for incremental updates.

    The metadata tracks file modification times and sizes to determine
    which files need re-indexing on subsequent runs.
    """

    META_FILE_NAME = ".index-meta.json"

    def __init__(self, index_dir: str | Path):
        """
        Initialize the metadata manager.

        Args:
            index_dir: Directory where index files are stored
        """
        self.index_dir = Path(index_dir)
        self.meta_path = self.index_dir / self.META_FILE_NAME
        self.data = self._load()

    def _load(self) -> IndexMetadata:
        """Load existing metadata or create new."""
        if self.meta_path.exists():
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    return IndexMetadata(
                        version=raw.get("version", "1.0"),
                        project_type=raw.get("project_type"),
                        created_at=raw.get("created_at"),
                        updated_at=raw.get("updated_at"),
                        files=raw.get("files", {}),
                    )
            except (json.JSONDecodeError, IOError):
                pass
        return IndexMetadata()

    def save(self) -> None:
        """Save metadata to disk."""
        self.data.updated_at = datetime.now().isoformat()
        self.index_dir.mkdir(parents=True, exist_ok=True)

        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.data), f, indent=2)

    def set_project_type(self, project_type: str) -> None:
        """Set the detected project type."""
        self.data.project_type = project_type

    def should_reindex(self, file_path: str | Path) -> bool:
        """
        Check if a file needs to be re-indexed.

        Args:
            file_path: Path to the file (relative to project root)

        Returns:
            True if the file should be re-indexed
        """
        file_path = str(file_path)
        abs_path = Path(file_path)

        if not abs_path.exists():
            return False

        record = self.data.files.get(file_path)
        if not record:
            return True

        stat = abs_path.stat()
        if record.get("mtime") != stat.st_mtime or record.get("size") != stat.st_size:
            return True

        return False

    def update_file_record(
        self,
        file_path: str | Path,
        index_file_path: str,
        checksum: Optional[str] = None,
    ) -> None:
        """
        Update the record for an indexed file.

        Args:
            file_path: Path to the source file
            index_file_path: Path to the index file containing this file's info
            checksum: Optional content hash
        """
        file_path = str(file_path)
        abs_path = Path(file_path)

        if not abs_path.exists():
            return

        stat = abs_path.stat()
        self.data.files[file_path] = {
            "mtime": stat.st_mtime,
            "size": stat.st_size,
            "indexed_in": index_file_path,
            "checksum": checksum,
        }

    def remove_record(self, file_path: str | Path) -> None:
        """Remove a file's record from metadata."""
        file_path = str(file_path)
        if file_path in self.data.files:
            del self.data.files[file_path]

    def get_files_in_directory(self, directory: str | Path) -> list[str]:
        """
        Get all indexed files within a directory.

        Args:
            directory: Directory path

        Returns:
            List of file paths within that directory
        """
        directory = str(directory)
        if not directory.endswith(os.sep):
            directory += os.sep

        return [f for f in self.data.files.keys() if f.startswith(directory)]

    def get_affected_index_files(self, file_paths: list[str]) -> set[str]:
        """
        Get the set of index files that contain any of the given source files.

        Args:
            file_paths: List of source file paths

        Returns:
            Set of index file paths that need updating
        """
        affected = set()
        for file_path in file_paths:
            record = self.data.files.get(file_path)
            if record and record.get("indexed_in"):
                affected.add(record["indexed_in"])
        return affected

    def get_deleted_files(self, current_files: set[str]) -> list[str]:
        """
        Find files that were previously indexed but no longer exist.

        Args:
            current_files: Set of currently existing file paths

        Returns:
            List of file paths that were deleted
        """
        return [f for f in self.data.files.keys() if f not in current_files]

    def cleanup_deleted(self, deleted_files: list[str]) -> None:
        """Remove records for deleted files."""
        for file_path in deleted_files:
            self.remove_record(file_path)
