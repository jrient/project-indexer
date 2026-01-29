"""
Python parser for extracting class and function definitions.
"""

import re
from .base import BaseParser, FileSignature


class PythonParser(BaseParser):
    """Parser for Python source files."""

    @property
    def extensions(self) -> list[str]:
        return [".py", ".pyi"]

    @property
    def language_name(self) -> str:
        return "Python"

    def parse(self, content: str) -> FileSignature:
        exports = []
        imports = []

        # Extract imports
        imports = self._extract_imports(content)

        # Extract top-level definitions
        exports = self._extract_definitions(content)

        return FileSignature(exports=exports, imports=imports)

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements."""
        imports = set()

        # Match: import module
        pattern = r"^import\s+(\w+)"
        for match in re.finditer(pattern, content, re.MULTILINE):
            imports.add(match.group(1))

        # Match: from module import ...
        pattern = r"^from\s+(\w+)(?:\.\w+)*\s+import"
        for match in re.finditer(pattern, content, re.MULTILINE):
            module = match.group(1)
            # Skip relative imports
            if module != ".":
                imports.add(module)

        return sorted(imports)

    def _extract_definitions(self, content: str) -> list[str]:
        """Extract class and function definitions."""
        exports = []
        lines = content.split("\n")

        current_class = None
        class_indent = 0

        for i, line in enumerate(lines):
            # Skip empty lines and comments
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue

            # Calculate indentation
            indent = len(line) - len(stripped)

            # Check if we're still inside a class
            if current_class and indent <= class_indent:
                current_class = None
                class_indent = 0

            # Match class definition
            class_match = re.match(r"^(\s*)class\s+(\w+)(?:\(([^)]*)\))?:", line)
            if class_match:
                indent_str = class_match.group(1)
                name = class_match.group(2)
                bases = class_match.group(3)

                # Only capture top-level classes
                if len(indent_str) == 0:
                    if bases:
                        bases = self._simplify_bases(bases)
                        exports.append(f"class {name}({bases})")
                    else:
                        exports.append(f"class {name}")

                    current_class = name
                    class_indent = len(indent_str)
                continue

            # Match function/method definition
            func_match = re.match(
                r"^(\s*)(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^\n:]+))?:",
                line,
            )
            if func_match:
                indent_str = func_match.group(1)
                is_async = func_match.group(2) or ""
                name = func_match.group(3)
                params = func_match.group(4)
                return_type = func_match.group(5)

                # Skip private methods (but keep dunder methods for classes)
                if name.startswith("_") and not name.startswith("__"):
                    continue

                # Simplify parameters
                params = self._simplify_params(params)

                # Format the signature
                async_prefix = "async " if is_async.strip() else ""
                if return_type:
                    return_type = return_type.strip()
                    sig = f"{async_prefix}def {name}({params}) -> {return_type}"
                else:
                    sig = f"{async_prefix}def {name}({params})"

                # Determine if it's a method or top-level function
                if current_class and len(indent_str) > class_indent:
                    # It's a method - add with indentation marker
                    exports.append(f"  {sig}")
                elif len(indent_str) == 0:
                    # Top-level function
                    exports.append(sig)

        return exports

    def _simplify_params(self, params: str) -> str:
        """Simplify function parameters for display."""
        if not params.strip():
            return ""

        simplified = []
        current = ""
        depth = 0

        for char in params:
            if char in "([{":
                depth += 1
                current += char
            elif char in ")]}":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                name = self._extract_param_name(current)
                if name:
                    simplified.append(name)
                current = ""
            else:
                current += char

        if current.strip():
            name = self._extract_param_name(current)
            if name:
                simplified.append(name)

        return ", ".join(simplified)

    def _extract_param_name(self, param: str) -> str:
        """Extract just the parameter name from a full parameter declaration."""
        param = param.strip()
        if not param:
            return ""

        # Skip *args and **kwargs style
        if param.startswith("*"):
            return param.split(":")[0].strip()

        # Handle name: Type = default
        match = re.match(r"(\w+)", param)
        return match.group(1) if match else ""

    def _simplify_bases(self, bases: str) -> str:
        """Simplify class base classes for display."""
        # Just extract the class names, ignore generic parameters
        parts = []
        for base in bases.split(","):
            base = base.strip()
            match = re.match(r"(\w+)", base)
            if match:
                parts.append(match.group(1))
        return ", ".join(parts)
