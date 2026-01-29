"""
Base parser interface and registry for language-specific parsers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


@dataclass
class FileSignature:
    """Represents extracted signatures from a file."""
    exports: list[str]
    imports: list[str]
    description: Optional[str] = None


class BaseParser(ABC):
    """Abstract base class for language-specific parsers."""

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """Return list of supported file extensions (e.g., ['.py', '.pyi'])."""
        pass

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name for display."""
        pass

    @abstractmethod
    def parse(self, content: str) -> FileSignature:
        """
        Parse file content and extract signatures.

        Args:
            content: The file content as string

        Returns:
            FileSignature with extracted exports and imports
        """
        pass

    def can_parse(self, file_path: str | Path) -> bool:
        """Check if this parser can handle the given file."""
        ext = Path(file_path).suffix.lower()
        return ext in self.extensions

    def format_markdown(self, signature: FileSignature) -> str:
        """Format the signature as markdown."""
        lines = []

        if signature.exports:
            lines.append("**Exports**:")
            for export in signature.exports:
                lines.append(f"- `{export}`")
        else:
            lines.append("_No exports detected_")

        if signature.imports:
            lines.append("")
            lines.append("**Dependencies**: " + ", ".join(f"`{imp}`" for imp in signature.imports[:5]))
            if len(signature.imports) > 5:
                lines.append(f"  _(+{len(signature.imports) - 5} more)_")

        return "\n".join(lines)


class ParserRegistry:
    """Registry for managing language parsers."""

    _parsers: list[BaseParser] = []

    @classmethod
    def register(cls, parser: BaseParser) -> None:
        """Register a parser instance."""
        cls._parsers.append(parser)

    @classmethod
    def get_parser(cls, file_path: str | Path) -> Optional[BaseParser]:
        """Get a parser that can handle the given file."""
        for parser in cls._parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get all supported file extensions."""
        extensions = []
        for parser in cls._parsers:
            extensions.extend(parser.extensions)
        return list(set(extensions))

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers."""
        cls._parsers = []
