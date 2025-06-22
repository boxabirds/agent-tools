"""Base parser interface for all code parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ParseResult:
    """Result of parsing operation."""
    
    language: str
    ast_text: str
    metadata: Dict[str, Any]
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if parsing was successful."""
        return self.error is None


class BaseParser(ABC):
    """Abstract base class for code parsers."""
    
    @abstractmethod
    async def parse(self, content: str, language: str) -> ParseResult:
        """Parse code content and return AST representation.
        
        Args:
            content: Source code to parse
            language: Programming language identifier
            
        Returns:
            ParseResult with AST text representation
        """
        pass
    
    @abstractmethod
    async def parse_file(self, file_path: str, language: Optional[str] = None) -> ParseResult:
        """Parse code from file.
        
        Args:
            file_path: Path to source file
            language: Optional language override (auto-detect if None)
            
        Returns:
            ParseResult with AST text representation
        """
        pass
    
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Return list of supported language identifiers."""
        pass
    
    @abstractmethod
    async def is_language_available(self, language: str) -> bool:
        """Check if language grammar is available/downloaded."""
        pass
    
    def format_ast(self, node: Any, indent: int = 0) -> str:
        """Format AST node as text (can be overridden)."""
        return self._default_format_ast(node, indent)
    
    def _default_format_ast(self, node: Any, indent: int = 0) -> str:
        """Default AST formatting implementation."""
        lines = []
        indent_str = "  " * indent
        
        if hasattr(node, 'type'):
            lines.append(f"{indent_str}{node.type}")
            
        if hasattr(node, 'children'):
            for child in node.children:
                lines.append(self._default_format_ast(child, indent + 1))
                
        return "\n".join(lines)


class ParserError(Exception):
    """Base exception for parser errors."""
    pass


class GrammarNotFoundError(ParserError):
    """Raised when language grammar cannot be found or downloaded."""
    pass


class LanguageNotSupportedError(ParserError):
    """Raised when language is not supported."""
    pass


class ParseError(ParserError):
    """Raised when code cannot be parsed."""
    pass