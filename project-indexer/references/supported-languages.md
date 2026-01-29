# Supported Languages Reference

## TypeScript / JavaScript

**Extensions**: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`

**Extracted Exports**:
- `export function name(params): ReturnType`
- `export class ClassName extends BaseClass`
- `export interface InterfaceName`
- `export type TypeName`
- `export const/let/var name: Type`
- `export enum EnumName`
- `export default ...`

**Extracted Imports**:
- External packages from `import ... from 'package'`
- Packages from `require('package')`

## Python

**Extensions**: `.py`, `.pyi`

**Extracted Definitions**:
- `class ClassName(BaseClass)`
- `def function_name(params) -> ReturnType`
- `async def async_function(params)`
- Class methods (indented under class)

**Notes**:
- Private members (starting with `_`) are excluded
- Dunder methods (`__init__`, etc.) are included
- Only top-level and first-level nested definitions are captured

## Adding New Language Support

To add support for a new language:

1. Create a new parser file in `scripts/parsers/`
2. Inherit from `BaseParser`
3. Implement `extensions`, `language_name`, and `parse()` methods
4. Register the parser in `scripts/parsers/__init__.py`
5. Update this reference document

Example parser structure:

```python
from .base import BaseParser, FileSignature

class NewLanguageParser(BaseParser):
    @property
    def extensions(self) -> list[str]:
        return [".ext1", ".ext2"]

    @property
    def language_name(self) -> str:
        return "New Language"

    def parse(self, content: str) -> FileSignature:
        exports = []
        imports = []
        # ... extraction logic ...
        return FileSignature(exports=exports, imports=imports)
```
