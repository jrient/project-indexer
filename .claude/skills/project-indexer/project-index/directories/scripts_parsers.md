# scripts\parsers

> Language parsers and code analyzers.

## Files

### __init__.py
**Path**: `scripts\parsers\__init__.py`
**Language**: Python

> Language parsers for extracting code signatures.

_No exports detected_

**Internal**: `.base`, `.typescript`, `.python_parser`, `.go_parser`

---

### base.py
**Path**: `scripts\parsers\base.py`
**Language**: Python

> Base parser interface and registry for language-specific parsers.

**Exports**:
- `@dataclass class FileSignature`
- `class BaseParser(ABC)`
- `  def extensions() -> list[str]`
- `  def language_name() -> str`
- `  @abstractmethod def parse(content) -> FileSignature`
- `  def can_parse(file_path) -> bool`
- `  def format_markdown(signature, high_density) -> str`
- `class ParserRegistry`
- `  @classmethod def register(parser) -> None`
- `  @classmethod def get_parser(file_path) -> Optional[BaseParser]`
- `  @classmethod def supported_extensions() -> list[str]`
- `  @classmethod def clear() -> None`

**Dependencies**: `__future__`, `abc`, `dataclasses`, `pathlib`, `typing`

---

### go_parser.py
**Path**: `scripts\parsers\go_parser.py`
**Language**: Python

> Go language parser for extracting struct, interface, and function definitions.

**Exports**:
- `class GoParser(BaseParser)`
- `  @property def extensions() -> list[str]`
- `  @property def language_name() -> str`
- `  def parse(content) -> FileSignature`

**Dependencies**: `__future__`, `re`, `typing`

**Internal**: `.base`

---

### python_parser.py
**Path**: `scripts\parsers\python_parser.py`
**Language**: Python

> Python parser using AST for accurate extraction of class and function definitions.

**Exports**:
- `class PythonParser(BaseParser)`
- `  @property def extensions() -> list[str]`
- `  @property def language_name() -> str`
- `  def parse(content) -> FileSignature`

**Dependencies**: `__future__`, `ast`, `typing`

**Internal**: `.base`

---

### typescript.py
**Path**: `scripts\parsers\typescript.py`
**Language**: Python

> TypeScript/JavaScript parser for extracting exports and signatures.

**Exports**:
- `class TypeScriptParser(BaseParser)`
- `  @property def extensions() -> list[str]`
- `  @property def language_name() -> str`
- `  def parse(content) -> FileSignature`

**Dependencies**: `re`

**Internal**: `.base`

---
