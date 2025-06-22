"""High-level API for agent-tools."""

from typing import Dict, List, Optional, Type

from agenttools.parsers.base import BaseParser, ParseResult
from agenttools.parsers.tree_sitter import TreeSitterParser


class AgentTools:
    """Main API class for agent-tools."""
    
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        self._default_parser: Optional[BaseParser] = None
        
        # Register default parsers
        self._register_default_parsers()
    
    def _register_default_parsers(self) -> None:
        """Register default parser implementations."""
        # Tree-sitter as default
        tree_sitter = TreeSitterParser()
        self.register_parser("tree-sitter", tree_sitter)
        self.set_default_parser("tree-sitter")
    
    def register_parser(self, name: str, parser: BaseParser) -> None:
        """Register a new parser implementation."""
        self._parsers[name] = parser
    
    def set_default_parser(self, name: str) -> None:
        """Set the default parser to use."""
        if name not in self._parsers:
            raise ValueError(f"Parser '{name}' not registered")
        self._default_parser = self._parsers[name]
    
    def get_parser(self, name: Optional[str] = None) -> BaseParser:
        """Get a parser by name or return default."""
        if name:
            if name not in self._parsers:
                raise ValueError(f"Parser '{name}' not found")
            return self._parsers[name]
        
        if not self._default_parser:
            raise ValueError("No default parser set")
        
        return self._default_parser
    
    async def parse_code(
        self, 
        content: str, 
        language: str,
        parser_name: Optional[str] = None
    ) -> ParseResult:
        """Parse code content.
        
        Args:
            content: Source code to parse
            language: Programming language
            parser_name: Optional specific parser to use
            
        Returns:
            ParseResult with AST representation
        """
        parser = self.get_parser(parser_name)
        return await parser.parse(content, language)
    
    async def parse_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        parser_name: Optional[str] = None
    ) -> ParseResult:
        """Parse code from file.
        
        Args:
            file_path: Path to source file
            language: Optional language override
            parser_name: Optional specific parser to use
            
        Returns:
            ParseResult with AST representation
        """
        parser = self.get_parser(parser_name)
        return await parser.parse_file(file_path, language)
    
    def supported_languages(self, parser_name: Optional[str] = None) -> List[str]:
        """Get list of supported languages."""
        parser = self.get_parser(parser_name)
        return parser.supported_languages()
    
    async def is_language_available(
        self,
        language: str,
        parser_name: Optional[str] = None
    ) -> bool:
        """Check if language is available."""
        parser = self.get_parser(parser_name)
        return await parser.is_language_available(language)
    
    def list_parsers(self) -> List[str]:
        """List all registered parsers."""
        return list(self._parsers.keys())


# Convenience functions for direct usage

_global_tools = AgentTools()


async def parse_code(content: str, language: str) -> ParseResult:
    """Parse code content using default parser."""
    return await _global_tools.parse_code(content, language)


async def parse_file(file_path: str, language: Optional[str] = None) -> ParseResult:
    """Parse code from file using default parser."""
    return await _global_tools.parse_file(file_path, language)


def supported_languages() -> List[str]:
    """Get list of supported languages."""
    return _global_tools.supported_languages()


async def is_language_available(language: str) -> bool:
    """Check if language is available."""
    return await _global_tools.is_language_available(language)