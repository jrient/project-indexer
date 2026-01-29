# scripts\utils

## Directory Purpose
_AI can describe the purpose of this directory here_

## Files

### __init__.py
**Path**: `scripts\utils\__init__.py`
**Language**: Python

_No exports detected_

---

### ignore.py
**Path**: `scripts\utils\ignore.py`
**Language**: Python

**Exports**:
- `class IgnorePatterns`
- `  def __init__(self, root_dir, custom_patterns)`
- `  def should_ignore(self, path) -> bool`
- `  def filter_paths(self, paths) -> list[Path]`

**Dependencies**: `__future__`, `fnmatch`, `os`, `pathlib`, `typing`

---

### meta.py
**Path**: `scripts\utils\meta.py`
**Language**: Python

**Exports**:
- `class FileRecord`
- `class IndexMetadata`
- `  def __post_init__(self)`
- `class MetaManager`
- `  def __init__(self, index_dir)`
- `  def save(self) -> None`
- `  def set_project_type(self, project_type) -> None`
- `  def should_reindex(self, file_path) -> bool`
- `  def remove_record(self, file_path) -> None`
- `  def get_files_in_directory(self, directory) -> list[str]`
- `  def get_affected_index_files(self, file_paths) -> set[str]`
- `  def get_deleted_files(self, current_files) -> list[str]`
- `  def cleanup_deleted(self, deleted_files) -> None`

**Dependencies**: `__future__`, `dataclasses`, `datetime`, `json`, `os`
  _(+2 more)_

---

### tree.py
**Path**: `scripts\utils\tree.py`
**Language**: Python

_No exports detected_

**Dependencies**: `__future__`, `os`, `pathlib`, `typing`

---
