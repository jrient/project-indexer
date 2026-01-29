"""
Language parsers for extracting code signatures.
"""

from .base import BaseParser, ParserRegistry, FileSignature
from .typescript import TypeScriptParser
from .python_parser import PythonParser
from .go_parser import GoParser

__all__ = [
    "BaseParser",
    "ParserRegistry",
    "FileSignature",
    "TypeScriptParser",
    "PythonParser",
    "GoParser",
]
