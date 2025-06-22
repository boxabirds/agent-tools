"""Unit tests for AgentTools API."""

import pytest

from mcp_code_parser.api import AgentTools
from mcp_code_parser.parsers.base import BaseParser, ParseResult


class MockParser(BaseParser):
    """Mock parser for testing."""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self.parse_called = False
        self.parse_file_called = False
    
    async def parse(self, content: str, language: str) -> ParseResult:
        self.parse_called = True
        return ParseResult(
            language=language,
            ast_text=f"Mock AST for {language}",
            metadata={"parser": self.name}
        )
    
    async def parse_file(self, file_path: str, language: str = None) -> ParseResult:
        self.parse_file_called = True
        return ParseResult(
            language=language or "mock",
            ast_text=f"Mock AST from {file_path}",
            metadata={"parser": self.name, "file": file_path}
        )
    
    def supported_languages(self) -> list:
        return ["mock", "test"]
    
    async def is_language_available(self, language: str) -> bool:
        return language in self.supported_languages()


@pytest.fixture
def mcp_code_parser():
    """Create AgentTools instance without default parsers."""
    tools = AgentTools()
    # Clear default parsers for testing
    tools._parsers.clear()
    tools._default_parser = None
    return tools


def test_register_parser(mcp_code_parser):
    """Test registering custom parsers."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    mcp_code_parser.register_parser("custom1", parser1)
    mcp_code_parser.register_parser("custom2", parser2)
    
    assert "custom1" in mcp_code_parser._parsers
    assert "custom2" in mcp_code_parser._parsers
    assert mcp_code_parser._parsers["custom1"] is parser1
    assert mcp_code_parser._parsers["custom2"] is parser2


def test_set_default_parser(mcp_code_parser):
    """Test setting default parser."""
    parser = MockParser()
    mcp_code_parser.register_parser("test", parser)
    
    # Should fail if parser not registered
    with pytest.raises(ValueError, match="Parser 'nonexistent' not registered"):
        mcp_code_parser.set_default_parser("nonexistent")
    
    # Should succeed if parser is registered
    mcp_code_parser.set_default_parser("test")
    assert mcp_code_parser._default_parser is parser


def test_get_parser(mcp_code_parser):
    """Test getting parsers."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    mcp_code_parser.register_parser("p1", parser1)
    mcp_code_parser.register_parser("p2", parser2)
    mcp_code_parser.set_default_parser("p1")
    
    # Get specific parser
    assert mcp_code_parser.get_parser("p2") is parser2
    
    # Get default parser
    assert mcp_code_parser.get_parser() is parser1
    
    # Error on non-existent parser
    with pytest.raises(ValueError, match="Parser 'invalid' not found"):
        mcp_code_parser.get_parser("invalid")
    
    # Error when no default set
    mcp_code_parser._default_parser = None
    with pytest.raises(ValueError, match="No default parser set"):
        mcp_code_parser.get_parser()


@pytest.mark.asyncio
async def test_parse_code_with_specific_parser(mcp_code_parser):
    """Test parsing code with specific parser."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    mcp_code_parser.register_parser("p1", parser1)
    mcp_code_parser.register_parser("p2", parser2)
    mcp_code_parser.set_default_parser("p1")
    
    # Use specific parser
    result = await mcp_code_parser.parse_code("test", "mock", parser_name="p2")
    assert parser2.parse_called
    assert not parser1.parse_called
    assert result.metadata["parser"] == "parser2"


@pytest.mark.asyncio
async def test_parse_code_with_default_parser(mcp_code_parser):
    """Test parsing code with default parser."""
    parser = MockParser()
    mcp_code_parser.register_parser("default", parser)
    mcp_code_parser.set_default_parser("default")
    
    result = await mcp_code_parser.parse_code("test", "mock")
    assert parser.parse_called
    assert result.success


@pytest.mark.asyncio
async def test_parse_file_with_language_override(mcp_code_parser):
    """Test parsing file with language override."""
    parser = MockParser()
    mcp_code_parser.register_parser("test", parser)
    mcp_code_parser.set_default_parser("test")
    
    result = await mcp_code_parser.parse_file("/test/file.txt", language="mock")
    assert parser.parse_file_called
    assert result.language == "mock"
    assert result.metadata["file"] == "/test/file.txt"


def test_list_parsers(mcp_code_parser):
    """Test listing registered parsers."""
    assert mcp_code_parser.list_parsers() == []
    
    mcp_code_parser.register_parser("p1", MockParser())
    mcp_code_parser.register_parser("p2", MockParser())
    
    parsers = mcp_code_parser.list_parsers()
    assert len(parsers) == 2
    assert "p1" in parsers
    assert "p2" in parsers


def test_supported_languages_delegation(mcp_code_parser):
    """Test that supported_languages delegates to parser."""
    parser = MockParser()
    mcp_code_parser.register_parser("test", parser)
    mcp_code_parser.set_default_parser("test")
    
    languages = mcp_code_parser.supported_languages()
    assert languages == ["mock", "test"]
    
    # With specific parser
    languages = mcp_code_parser.supported_languages(parser_name="test")
    assert languages == ["mock", "test"]


@pytest.mark.asyncio
async def test_is_language_available_delegation(mcp_code_parser):
    """Test that is_language_available delegates to parser."""
    parser = MockParser()
    mcp_code_parser.register_parser("test", parser)
    mcp_code_parser.set_default_parser("test")
    
    assert await mcp_code_parser.is_language_available("mock") is True
    assert await mcp_code_parser.is_language_available("invalid") is False


def test_default_parser_initialization():
    """Test that AgentTools initializes with tree-sitter by default."""
    tools = AgentTools()
    
    assert "tree-sitter" in tools._parsers
    assert tools._default_parser is not None
    assert tools.list_parsers() == ["tree-sitter"]
    
    # Should be able to get supported languages
    languages = tools.supported_languages()
    assert "python" in languages
    assert "javascript" in languages


@pytest.mark.asyncio
async def test_error_propagation(mcp_code_parser):
    """Test that parser errors are properly propagated."""
    class ErrorParser(MockParser):
        async def parse(self, content: str, language: str) -> ParseResult:
            return ParseResult(
                language=language,
                ast_text="",
                metadata={},
                error="Test error"
            )
    
    parser = ErrorParser()
    mcp_code_parser.register_parser("error", parser)
    mcp_code_parser.set_default_parser("error")
    
    result = await mcp_code_parser.parse_code("test", "any")
    assert not result.success
    assert result.error == "Test error"