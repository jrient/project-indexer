# scripts\utils

> Utility functions and helpers.

## Files

### __init__.py
**Path**: `scripts\utils\__init__.py`
**Language**: Python

> Utility modules for project indexer.

_No exports detected_

**Internal**: `.tree`, `.meta`, `.ignore`, `.inference`

---

### ignore.py
**Path**: `scripts\utils\ignore.py`
**Language**: Python

> Gitignore-style pattern matching for file filtering.

**Exports**:
- `class IgnorePatterns`
- `  def __init__(root_dir, custom_patterns)`
- `  def should_ignore(path) -> bool`
- `  def filter_paths(paths) -> list[Path]`

**Dependencies**: `__future__`, `fnmatch`, `os`, `pathlib`, `typing`

---

### inference.py
**Path**: `scripts\utils\inference.py`
**Language**: Python

> Heuristic inference for directory purposes.

**Exports**:
- `def infer_directory_purpose(rel_path, filenames, root_dir) -> str`

**Dependencies**: `__future__`, `pathlib`, `typing`

---

### meta.py
**Path**: `scripts\utils\meta.py`
**Language**: Python

> Metadata management for incremental indexing using SQLite.

**Exports**:
- `class MetaManager`
- `  def __init__(index_dir)`
- `  def set_project_type(project_type) -> None`
- `  def get_project_type() -> Optional[str]`
- `  def should_reindex(file_path) -> bool`
- `  def update_file_record(file_path, index_file_path, checksum, symbols) -> None`
- `  def remove_record(file_path) -> None`
- `  def get_files_in_directory(directory) -> list[str]`
- `  def get_affected_index_files(file_paths) -> set[str]`
- `  def search(query, limit) -> list[tuple[str, str, str]]`
- `  def get_deleted_files(current_files) -> list[str]`
- `  def cleanup_deleted(deleted_files) -> None`
- `  def get_stats() -> dict`
- `  def save() -> None`

**Dependencies**: `__future__`, `contextlib`, `datetime`, `os`, `pathlib`
  _(+2 more)_

---

### tree.py
**Path**: `scripts\utils\tree.py`
**Language**: Python

> Directory tree generator for project visualization.

**Exports**:
- `def generate_tree(root_dir, should_ignore, max_depth, show_files, max_files_per_dir) -> str`
- `def generate_compact_tree(root_dir, should_ignore, max_depth) -> str`

**Dependencies**: `__future__`, `os`, `pathlib`, `typing`

---
