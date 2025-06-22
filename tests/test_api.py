"""Unit tests for AgentTools API."""

import pytest

from agenttools.api import AgentTools
from agenttools.parsers.base import BaseParser, ParseResult


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
def agent_tools():
    """Create AgentTools instance without default parsers."""
    tools = AgentTools()
    # Clear default parsers for testing
    tools._parsers.clear()
    tools._default_parser = None
    return tools


def test_register_parser(agent_tools):
    """Test registering custom parsers."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    agent_tools.register_parser("custom1", parser1)
    agent_tools.register_parser("custom2", parser2)
    
    assert "custom1" in agent_tools._parsers
    assert "custom2" in agent_tools._parsers
    assert agent_tools._parsers["custom1"] is parser1
    assert agent_tools._parsers["custom2"] is parser2


def test_set_default_parser(agent_tools):
    """Test setting default parser."""
    parser = MockParser()
    agent_tools.register_parser("test", parser)
    
    # Should fail if parser not registered
    with pytest.raises(ValueError, match="Parser 'nonexistent' not registered"):
        agent_tools.set_default_parser("nonexistent")
    
    # Should succeed if parser is registered
    agent_tools.set_default_parser("test")
    assert agent_tools._default_parser is parser


def test_get_parser(agent_tools):
    """Test getting parsers."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    agent_tools.register_parser("p1", parser1)
    agent_tools.register_parser("p2", parser2)
    agent_tools.set_default_parser("p1")
    
    # Get specific parser
    assert agent_tools.get_parser("p2") is parser2
    
    # Get default parser
    assert agent_tools.get_parser() is parser1
    
    # Error on non-existent parser
    with pytest.raises(ValueError, match="Parser 'invalid' not found"):
        agent_tools.get_parser("invalid")
    
    # Error when no default set
    agent_tools._default_parser = None
    with pytest.raises(ValueError, match="No default parser set"):
        agent_tools.get_parser()


@pytest.mark.asyncio
async def test_parse_code_with_specific_parser(agent_tools):
    """Test parsing code with specific parser."""
    parser1 = MockParser("parser1")
    parser2 = MockParser("parser2")
    
    agent_tools.register_parser("p1", parser1)
    agent_tools.register_parser("p2", parser2)
    agent_tools.set_default_parser("p1")
    
    # Use specific parser
    result = await agent_tools.parse_code("test", "mock", parser_name="p2")
    assert parser2.parse_called
    assert not parser1.parse_called
    assert result.metadata["parser"] == "parser2"


@pytest.mark.asyncio
async def test_parse_code_with_default_parser(agent_tools):
    """Test parsing code with default parser."""
    parser = MockParser()
    agent_tools.register_parser("default", parser)
    agent_tools.set_default_parser("default")
    
    result = await agent_tools.parse_code("test", "mock")
    assert parser.parse_called
    assert result.success


@pytest.mark.asyncio
async def test_parse_file_with_language_override(agent_tools):
    """Test parsing file with language override."""
    parser = MockParser()
    agent_tools.register_parser("test", parser)
    agent_tools.set_default_parser("test")
    
    result = await agent_tools.parse_file("/test/file.txt", language="mock")
    assert parser.parse_file_called
    assert result.language == "mock"
    assert result.metadata["file"] == "/test/file.txt"


def test_list_parsers(agent_tools):
    """Test listing registered parsers."""
    assert agent_tools.list_parsers() == []
    
    agent_tools.register_parser("p1", MockParser())
    agent_tools.register_parser("p2", MockParser())
    
    parsers = agent_tools.list_parsers()
    assert len(parsers) == 2
    assert "p1" in parsers
    assert "p2" in parsers


def test_supported_languages_delegation(agent_tools):
    """Test that supported_languages delegates to parser."""
    parser = MockParser()
    agent_tools.register_parser("test", parser)
    agent_tools.set_default_parser("test")
    
    languages = agent_tools.supported_languages()
    assert languages == ["mock", "test"]
    
    # With specific parser
    languages = agent_tools.supported_languages(parser_name="test")
    assert languages == ["mock", "test"]


@pytest.mark.asyncio
async def test_is_language_available_delegation(agent_tools):
    """Test that is_language_available delegates to parser."""
    parser = MockParser()
    agent_tools.register_parser("test", parser)
    agent_tools.set_default_parser("test")
    
    assert await agent_tools.is_language_available("mock") is True
    assert await agent_tools.is_language_available("invalid") is False


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
async def test_error_propagation(agent_tools):
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
    agent_tools.register_parser("error", parser)
    agent_tools.set_default_parser("error")
    
    result = await agent_tools.parse_code("test", "any")
    assert not result.success
    assert result.error == "Test error"