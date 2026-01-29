"""
TypeScript/JavaScript parser for extracting exports and signatures.
"""

import re
from .base import BaseParser, FileSignature, ExportItem


class TypeScriptParser(BaseParser):
    """Parser for TypeScript, JavaScript, and JSX/TSX files."""

    @property
    def extensions(self) -> list[str]:
        return [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]

    @property
    def language_name(self) -> str:
        return "TypeScript/JavaScript"

    def parse(self, content: str) -> FileSignature:
        imports = self._extract_imports(content)
        exports = self._extract_exports(content)
        return FileSignature(exports=exports, imports=imports)

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements."""
        imports = set()

        # Match: import ... from 'module'
        pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(pattern, content, re.MULTILINE):
            module = match.group(1)
            # Only keep external modules (not relative imports)
            if not module.startswith("."):
                imports.add(module)

        # Match: require('module')
        pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        for match in re.finditer(pattern, content, re.MULTILINE):
            module = match.group(1)
            if not module.startswith("."):
                imports.add(module)

        return sorted(imports)

    def _extract_exports(self, content: str) -> list[ExportItem]:
        """Extract exported declarations."""
        exports: list[ExportItem] = []

        # Pattern for exported function declarations
        func_pattern = r"export\s+(async\s+)?function\s+(\w+)\s*(<[^>]*>)?\s*\(([^)]*)\)(?:\s*:\s*([^\n{]+))?"
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            is_async = match.group(1) or ""
            name = match.group(2)
            generics = match.group(3) or ""
            params = self._simplify_params(match.group(4) or "")
            return_type = match.group(5) or ""
            if return_type:
                return_type = return_type.strip()
                sig = f"{is_async.strip()}function {name}{generics}({params}): {return_type}".strip()
            else:
                sig = f"{is_async.strip()}function {name}{generics}({params})".strip()
            exports.append(ExportItem(signature=sig))

        # Pattern for exported class declarations
        class_pattern = r"export\s+(?:abstract\s+)?class\s+(\w+)(?:<[^>]*>)?(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^\n{]+))?"
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            sig = f"class {name} extends {extends}" if extends else f"class {name}"
            exports.append(ExportItem(signature=sig))

        # Pattern for exported interface declarations
        interface_pattern = r"export\s+interface\s+(\w+)(?:<[^>]*>)?"
        for match in re.finditer(interface_pattern, content, re.MULTILINE):
            name = match.group(1)
            exports.append(ExportItem(signature=f"interface {name}"))

        # Pattern for exported type alias
        type_pattern = r"export\s+type\s+(\w+)(?:<[^>]*>)?\s*="
        for match in re.finditer(type_pattern, content, re.MULTILINE):
            name = match.group(1)
            exports.append(ExportItem(signature=f"type {name}"))

        # Pattern for exported const/let/var
        var_pattern = r"export\s+(const|let|var)\s+(\w+)(?:\s*:\s*([^=\n]+))?\s*="
        for match in re.finditer(var_pattern, content, re.MULTILINE):
            kind = match.group(1)
            name = match.group(2)
            type_hint = match.group(3)
            if type_hint:
                sig = f"{kind} {name}: {type_hint.strip()}"
            else:
                sig = f"{kind} {name}"
            exports.append(ExportItem(signature=sig))

        # Pattern for exported enum
        enum_pattern = r"export\s+enum\s+(\w+)"
        for match in re.finditer(enum_pattern, content, re.MULTILINE):
            name = match.group(1)
            exports.append(ExportItem(signature=f"enum {name}"))

        # Pattern for default export
        if re.search(r"export\s+default\s+", content):
            default_class = re.search(r"export\s+default\s+class\s+(\w+)", content)
            default_func = re.search(r"export\s+default\s+(?:async\s+)?function\s+(\w+)", content)
            if default_class:
                exports.append(ExportItem(signature=f"default class {default_class.group(1)}"))
            elif default_func:
                exports.append(ExportItem(signature=f"default function {default_func.group(1)}"))
            else:
                exports.append(ExportItem(signature="default export"))

        return exports

    def _simplify_params(self, params: str) -> str:
        """Simplify function parameters for display."""
        if not params.strip():
            return ""

        # Split by comma, keeping track of nested brackets
        simplified = []
        current = ""
        depth = 0

        for char in params:
            if char in "(<{":
                depth += 1
                current += char
            elif char in ")>}":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                simplified.append(self._extract_param_name(current))
                current = ""
            else:
                current += char

        if current.strip():
            simplified.append(self._extract_param_name(current))

        return ", ".join(simplified)

    def _extract_param_name(self, param: str) -> str:
        """Extract just the parameter name from a full parameter declaration."""
        param = param.strip()
        if not param:
            return ""

        # Handle destructuring: { a, b } or [a, b]
        if param.startswith("{") or param.startswith("["):
            return param.split(":")[0].strip() if ":" in param else param

        # Handle normal params: name: Type or name?: Type
        match = re.match(r"(\w+)\??", param)
        return match.group(1) if match else param
