"""
Python parser using AST for accurate extraction of class and function definitions.

This parser uses Python's built-in ast module instead of regex for:
- Accurate handling of multi-line signatures
- Proper decorator detection
- Docstring extraction
- Nested class/function support
"""

from __future__ import annotations

import ast
from typing import Optional

from .base import BaseParser, FileSignature, ExportItem


class PythonParser(BaseParser):
    """Parser for Python source files using AST."""

    @property
    def extensions(self) -> list[str]:
        return [".py", ".pyi"]

    @property
    def language_name(self) -> str:
        return "Python"

    def parse(self, content: str) -> FileSignature:
        """
        Parse Python source code and extract signatures.

        Args:
            content: Python source code as string

        Returns:
            FileSignature with exports, imports, and docstrings
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback for invalid Python syntax
            return FileSignature(exports=[], imports=[], module_doc="_Syntax error_")

        exports: list[ExportItem] = []
        imports: set[str] = set()
        internal_deps: list[str] = []

        # Module-level docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            module_doc = module_doc.split('\n')[0].strip()

        # Process top-level nodes
        for node in ast.iter_child_nodes(tree):
            self._process_node(node, exports, imports, internal_deps)

        return FileSignature(
            exports=exports,
            imports=sorted(imports),
            module_doc=module_doc,
            internal_deps=internal_deps,
        )

    def _process_node(
        self,
        node: ast.AST,
        exports: list[ExportItem],
        imports: set[str],
        internal_deps: list[str],
        class_name: Optional[str] = None,
    ) -> None:
        """Process a single AST node."""

        # Import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.level > 0:
                    internal_deps.append(f".{node.module}" if node.module else ".")
                else:
                    imports.add(node.module.split('.')[0])

        # Class definitions
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_') or node.name.startswith('__'):
                bases = [self._get_name(b) for b in node.bases if self._get_name(b)]
                base_str = f"({', '.join(bases)})" if bases else ""
                decorators = self._get_decorators(node)
                decorator_prefix = f"@{', @'.join(decorators)} " if decorators else ""

                signature = f"{decorator_prefix}class {node.name}{base_str}"
                class_doc = ast.get_docstring(node)
                docstring = class_doc.split('\n')[0].strip() if class_doc else None

                exports.append(ExportItem(signature=signature, docstring=docstring))

                # Process class methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self._process_function(item, exports, class_name=node.name)

        # Top-level function definitions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if class_name is None:
                self._process_function(node, exports)

    def _process_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        exports: list[ExportItem],
        class_name: Optional[str] = None,
    ) -> None:
        """Process a function or method definition."""
        name = node.name

        # Skip private methods (but keep dunder methods)
        if name.startswith('_') and not name.startswith('__'):
            return

        # Skip internal dunder methods except __init__
        if name.startswith('__') and name != '__init__':
            if name not in ('__str__', '__repr__', '__eq__', '__hash__', '__call__'):
                return

        # Build function signature
        async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        args = self._format_args(node.args)
        return_type = self._get_annotation(node.returns) if node.returns else ""
        return_suffix = f" -> {return_type}" if return_type else ""

        # Get decorators
        decorators = self._get_decorators(node)

        # Format based on whether it's a method or function
        if class_name:
            indent = "  "
            decorator_info = f"@{decorators[0]} " if decorators else ""
            signature = f"{indent}{decorator_info}{async_prefix}def {name}({args}){return_suffix}"
        else:
            decorator_prefix = f"@{', @'.join(decorators)} " if decorators else ""
            signature = f"{decorator_prefix}{async_prefix}def {name}({args}){return_suffix}"

        # Function docstring
        func_doc = ast.get_docstring(node)
        docstring = func_doc.split('\n')[0].strip() if func_doc else None

        exports.append(ExportItem(signature=signature, docstring=docstring))

    def _get_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
        """Extract decorator names."""
        decorators = []
        for decorator in node.decorator_list:
            name = self._get_name(decorator)
            if name and name not in ('overload',):  # Skip verbose decorators
                decorators.append(name)
        return decorators

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_annotation(self, node: ast.AST) -> str:
        """Extract type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value) if isinstance(node.value, str) else str(node.value)
        elif isinstance(node, ast.Attribute):
            value = self._get_annotation(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            slice_val = self._get_annotation(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation(e) for e in node.elts]
            return ", ".join(elements)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Union type with | syntax
            left = self._get_annotation(node.left)
            right = self._get_annotation(node.right)
            return f"{left} | {right}"
        return ""

    def _format_args(self, args: ast.arguments) -> str:
        """Format function arguments for display."""
        arg_parts = []

        # Regular arguments
        for arg in args.args:
            if arg.arg != 'self' and arg.arg != 'cls':
                arg_parts.append(arg.arg)

        # *args
        if args.vararg:
            arg_parts.append(f"*{args.vararg.arg}")

        # **kwargs
        if args.kwarg:
            arg_parts.append(f"**{args.kwarg.arg}")

        return ", ".join(arg_parts)
