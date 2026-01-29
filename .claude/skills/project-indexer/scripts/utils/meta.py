"""
Metadata management for incremental indexing using SQLite.

This module provides robust metadata storage for tracking:
- File modification times and sizes
- Index file associations
- Symbol search index
- Project configuration
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator


class MetaManager:
    """
    Manages index metadata using SQLite for incremental updates.

    SQLite provides better performance for large projects (10k+ files)
    compared to JSON-based storage, and supports concurrent access.
    """

    DB_NAME = "index_meta.db"
    SCHEMA_VERSION = 2

    def __init__(self, index_dir: str | Path):
        """
        Initialize the metadata manager.

        Args:
            index_dir: Directory where index files are stored
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.index_dir / self.DB_NAME
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database and create tables."""
        with self._get_conn() as conn:
            # Files table - tracks indexed source files
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    mtime REAL NOT NULL,
                    size INTEGER NOT NULL,
                    indexed_in TEXT,
                    checksum TEXT,
                    symbols TEXT
                )
            ''')

            # Project metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Search index table for symbol lookup
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    kind TEXT,
                    context TEXT
                )
            ''')

            # Create indexes for faster searches
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_symbol
                ON search_index(symbol)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_path
                ON search_index(path)
            ''')

            # Set schema version
            conn.execute(
                "INSERT OR REPLACE INTO project (key, value) VALUES (?, ?)",
                ("schema_version", str(self.SCHEMA_VERSION))
            )

            # Set creation time if not exists
            conn.execute('''
                INSERT OR IGNORE INTO project (key, value)
                VALUES (?, ?)
            ''', ("created_at", datetime.now().isoformat()))

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with automatic commit/rollback."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def set_project_type(self, project_type: str) -> None:
        """Set the detected project type."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO project (key, value) VALUES (?, ?)",
                ("project_type", project_type)
            )

    def get_project_type(self) -> Optional[str]:
        """Get the stored project type."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT value FROM project WHERE key = ?",
                ("project_type",)
            )
            row = cursor.fetchone()
            return row["value"] if row else None

    def should_reindex(self, file_path: str | Path) -> bool:
        """
        Check if a file needs to be re-indexed.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be re-indexed
        """
        file_path = str(file_path)
        abs_path = Path(file_path)

        if not abs_path.exists():
            return False

        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT mtime, size FROM files WHERE path = ?",
                (file_path,)
            )
            row = cursor.fetchone()

            if not row:
                return True

            stat = abs_path.stat()
            if row["mtime"] != stat.st_mtime or row["size"] != stat.st_size:
                return True

        return False

    def update_file_record(
        self,
        file_path: str | Path,
        index_file_path: str,
        checksum: Optional[str] = None,
        symbols: Optional[list[str]] = None,
    ) -> None:
        """
        Update the record for an indexed file.

        Args:
            file_path: Path to the source file
            index_file_path: Path to the index file containing this file's info
            checksum: Optional content hash
            symbols: Optional list of exported symbols for search
        """
        file_path = str(file_path)
        abs_path = Path(file_path)

        if not abs_path.exists():
            return

        stat = abs_path.stat()
        symbols_str = ",".join(symbols) if symbols else ""

        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO files
                (path, mtime, size, indexed_in, checksum, symbols)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_path, stat.st_mtime, stat.st_size,
                  index_file_path, checksum, symbols_str))

            # Update search index
            if symbols:
                # Remove old entries for this file
                conn.execute(
                    "DELETE FROM search_index WHERE path = ?",
                    (file_path,)
                )
                # Add new entries
                for symbol in symbols:
                    # Extract kind from symbol (e.g., "class Foo" -> kind="class", symbol="Foo")
                    parts = symbol.strip().split(maxsplit=1)
                    kind = parts[0] if len(parts) > 1 else "symbol"
                    name = parts[1].split("(")[0] if len(parts) > 1 else symbol
                    conn.execute('''
                        INSERT INTO search_index (path, symbol, kind, context)
                        VALUES (?, ?, ?, ?)
                    ''', (file_path, name, kind, symbol))

    def remove_record(self, file_path: str | Path) -> None:
        """Remove a file's record from metadata."""
        file_path = str(file_path)
        with self._get_conn() as conn:
            conn.execute("DELETE FROM files WHERE path = ?", (file_path,))
            conn.execute("DELETE FROM search_index WHERE path = ?", (file_path,))

    def get_files_in_directory(self, directory: str | Path) -> list[str]:
        """
        Get all indexed files within a directory.

        Args:
            directory: Directory path

        Returns:
            List of file paths within that directory
        """
        directory = str(directory)
        if not directory.endswith(os.sep) and not directory.endswith("/"):
            directory += os.sep

        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT path FROM files WHERE path LIKE ?",
                (f"{directory}%",)
            )
            return [row["path"] for row in cursor.fetchall()]

    def get_affected_index_files(self, file_paths: list[str]) -> set[str]:
        """
        Get the set of index files that contain any of the given source files.

        Args:
            file_paths: List of source file paths

        Returns:
            Set of index file paths that need updating
        """
        if not file_paths:
            return set()

        placeholders = ",".join("?" * len(file_paths))
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"SELECT DISTINCT indexed_in FROM files WHERE path IN ({placeholders})",
                file_paths
            )
            return {row["indexed_in"] for row in cursor.fetchall() if row["indexed_in"]}

    def search(self, query: str, limit: int = 20) -> list[tuple[str, str, str]]:
        """
        Search for symbols matching the query.

        Args:
            query: Search query (supports partial matching)
            limit: Maximum number of results

        Returns:
            List of (file_path, symbol_name, context) tuples
        """
        with self._get_conn() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT path, symbol, context
                FROM search_index
                WHERE symbol LIKE ? OR context LIKE ?
                LIMIT ?
            ''', (f"%{query}%", f"%{query}%", limit))
            return [(row["path"], row["symbol"], row["context"])
                    for row in cursor.fetchall()]

    def get_deleted_files(self, current_files: set[str]) -> list[str]:
        """
        Find files that were previously indexed but no longer exist.

        Args:
            current_files: Set of currently existing file paths

        Returns:
            List of file paths that were deleted
        """
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT path FROM files")
            all_indexed = {row["path"] for row in cursor.fetchall()}
            return [f for f in all_indexed if f not in current_files]

    def cleanup_deleted(self, deleted_files: list[str]) -> None:
        """Remove records for deleted files."""
        for file_path in deleted_files:
            self.remove_record(file_path)

    def get_stats(self) -> dict:
        """Get index statistics."""
        with self._get_conn() as conn:
            file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            symbol_count = conn.execute("SELECT COUNT(*) FROM search_index").fetchone()[0]
            created = conn.execute(
                "SELECT value FROM project WHERE key = ?",
                ("created_at",)
            ).fetchone()

            return {
                "total_files": file_count,
                "total_symbols": symbol_count,
                "created_at": created["value"] if created else None,
            }

    def save(self) -> None:
        """
        Compatibility method - SQLite auto-commits.
        Updates the last modified timestamp.
        """
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO project (key, value) VALUES (?, ?)",
                ("updated_at", datetime.now().isoformat())
            )
