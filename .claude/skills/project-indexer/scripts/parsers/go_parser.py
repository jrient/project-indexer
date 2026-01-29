"""
Go language parser for extracting struct, interface, and function definitions.

Extracts:
- Package name
- Import statements
- Struct definitions with fields
- Interface definitions
- Function signatures (exported only - capitalized names)
- Method receivers
- Doc comments
"""

from __future__ import annotations

import re
from typing import Optional

from .base import BaseParser, FileSignature, ExportItem


class GoParser(BaseParser):
    """Parser for Go source files."""

    @property
    def extensions(self) -> list[str]:
        return [".go"]

    @property
    def language_name(self) -> str:
        return "Go"

    def parse(self, content: str) -> FileSignature:
        """
        Parse Go source code and extract signatures.

        Args:
            content: Go source code as string

        Returns:
            FileSignature with exports, imports, and module_doc
        """
        exports: list[ExportItem] = []
        imports: list[str] = []
        module_doc = None

        # Extract package name
        pkg_match = re.search(r'^package\s+(\w+)', content, re.MULTILINE)
        if pkg_match:
            module_doc = f"Package: {pkg_match.group(1)}"

        # Extract imports
        imports = self._extract_imports(content)

        # Extract type definitions (struct/interface)
        self._extract_types(content, exports)

        # Extract functions
        self._extract_functions(content, exports)

        return FileSignature(
            exports=exports,
            imports=sorted(imports),
            module_doc=module_doc,
        )

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements."""
        imports = set()

        # Single import: import "fmt"
        single_pattern = r'^import\s+"([^"]+)"'
        for match in re.finditer(single_pattern, content, re.MULTILINE):
            imports.add(self._simplify_import(match.group(1)))

        # Block import: import ( ... )
        block_pattern = r'import\s*\(([\s\S]*?)\)'
        for match in re.finditer(block_pattern, content):
            block = match.group(1)
            for line in block.splitlines():
                line = line.strip()
                if line and not line.startswith('//'):
                    # Handle aliased imports: alias "package"
                    import_match = re.search(r'"([^"]+)"', line)
                    if import_match:
                        imports.add(self._simplify_import(import_match.group(1)))

        return list(imports)

    def _simplify_import(self, path: str) -> str:
        """Simplify import path to package name."""
        # Extract last part of path: github.com/user/pkg -> pkg
        parts = path.split('/')
        return parts[-1] if parts else path

    def _extract_types(self, content: str, exports: list[ExportItem]) -> None:
        """Extract struct and interface definitions."""
        type_pattern = r'(?://\s*([^\n]*)\n)?type\s+(\w+)\s+(struct|interface)\s*\{'

        for match in re.finditer(type_pattern, content):
            doc_comment = match.group(1)
            name = match.group(2)
            kind = match.group(3)

            if name[0].isupper():
                signature = f"type {name} {kind}"
                docstring = doc_comment.strip() if doc_comment else None
                exports.append(ExportItem(signature=signature, docstring=docstring))

        # Handle type aliases
        alias_pattern = r'type\s+(\w+)\s*=\s*(\w+)'
        for match in re.finditer(alias_pattern, content):
            name = match.group(1)
            target = match.group(2)
            if name[0].isupper():
                exports.append(ExportItem(signature=f"type {name} = {target}"))

    def _extract_functions(self, content: str, exports: list[ExportItem]) -> None:
        """Extract function and method definitions."""
        func_pattern = r'''
            (?://\s*([^\n]*)\n)?  # Optional doc comment
            func\s+
            (?:\(([^)]*)\)\s*)?  # Optional receiver
            (\w+)\s*             # Function name
            \(([^)]*)\)          # Parameters
            (?:\s*\(([^)]*)\)|\s*(\w+))?  # Optional return type(s)
        '''

        for match in re.finditer(func_pattern, content, re.VERBOSE):
            doc_comment = match.group(1)
            receiver = match.group(2)
            name = match.group(3)
            params = match.group(4)
            returns_multi = match.group(5)
            returns_single = match.group(6)

            if not name[0].isupper():
                continue

            params_simplified = self._simplify_params(params)
            returns = returns_multi or returns_single or ""

            if receiver:
                receiver_simplified = self._simplify_receiver(receiver)
                sig = f"func ({receiver_simplified}) {name}({params_simplified})"
            else:
                sig = f"func {name}({params_simplified})"

            if returns:
                returns_simplified = self._simplify_returns(returns)
                sig += f" {returns_simplified}"

            docstring = doc_comment.strip() if doc_comment else None
            exports.append(ExportItem(signature=sig, docstring=docstring))

    def _simplify_params(self, params: str) -> str:
        """Simplify function parameters."""
        if not params.strip():
            return ""

        # Extract just parameter names with types
        simplified = []
        for param in params.split(','):
            param = param.strip()
            if param:
                # Go params can be: name type, name1, name2 type, or just type
                parts = param.split()
                if len(parts) >= 2:
                    # name type or *type
                    simplified.append(f"{parts[0]} {parts[-1]}")
                elif parts:
                    simplified.append(parts[0])

        return ", ".join(simplified)

    def _simplify_receiver(self, receiver: str) -> str:
        """Simplify method receiver."""
        receiver = receiver.strip()
        parts = receiver.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1]}"
        return receiver

    def _simplify_returns(self, returns: str) -> str:
        """Simplify return type(s)."""
        returns = returns.strip()
        if ',' in returns:
            # Multiple returns: (type1, type2)
            types = [t.strip().split()[-1] for t in returns.split(',')]
            return f"({', '.join(types)})"
        return returns
