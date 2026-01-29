"""
Language parsers for extracting code signatures.
"""

from .base import BaseParser, ParserRegistry
from .typescript import TypeScriptParser
from .python_parser import PythonParser

__all__ = ["BaseParser", "ParserRegistry", "TypeScriptParser", "PythonParser"]
