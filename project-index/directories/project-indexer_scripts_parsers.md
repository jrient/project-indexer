# project-indexer\scripts\parsers

## Directory Purpose
_AI can describe the purpose of this directory here_

## Files

### __init__.py
**Path**: `project-indexer\scripts\parsers\__init__.py`
**Language**: Python

_No exports detected_

---

### base.py
**Path**: `project-indexer\scripts\parsers\base.py`
**Language**: Python

**Exports**:
- `class FileSignature`
- `class BaseParser(ABC)`
- `  def extensions(self) -> list[str]`
- `  def language_name(self) -> str`
- `  def parse(self, content) -> FileSignature`
- `  def can_parse(self, file_path) -> bool`
- `  def format_markdown(self, signature) -> str`
- `class ParserRegistry`
- `  def register(cls, parser) -> None`
- `  def get_parser(cls, file_path) -> Optional[BaseParser]`
- `  def supported_extensions(cls) -> list[str]`
- `  def clear(cls) -> None`

**Dependencies**: `__future__`, `abc`, `dataclasses`, `pathlib`, `typing`

---

### python_parser.py
**Path**: `project-indexer\scripts\parsers\python_parser.py`
**Language**: Python

**Exports**:
- `class PythonParser(BaseParser)`
- `  def extensions(self) -> list[str]`
- `  def language_name(self) -> str`
- `  def parse(self, content) -> FileSignature`

**Dependencies**: `re`

---

### typescript.py
**Path**: `project-indexer\scripts\parsers\typescript.py`
**Language**: Python

**Exports**:
- `class TypeScriptParser(BaseParser)`
- `  def extensions(self) -> list[str]`
- `  def language_name(self) -> str`
- `  def parse(self, content) -> FileSignature`

**Dependencies**: `re`

---
