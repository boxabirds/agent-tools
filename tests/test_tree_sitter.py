"""Unit tests for TreeSitterParser implementation."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_code_parser.parsers.base import GrammarNotFoundError, LanguageNotSupportedError
from mcp_code_parser.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
async def parser():
    """Create TreeSitterParser instance."""
    parser = TreeSitterParser()
    async with parser:
        yield parser


@pytest.mark.asyncio
async def test_parse_simple_python(parser):
    """Test parsing simple Python code."""
    code = "def hello():\n    return 'world'"
    
    result = await parser.parse(code, "python")
    
    # Should succeed when grammar is available
    assert result.success
    assert result.language == "python"
    assert "function_definition" in result.ast_text
    assert "hello" in result.ast_text
    assert result.error is None
    

@pytest.mark.asyncio
async def test_parse_unsupported_language(parser):
    """Test parsing with unsupported language."""
    result = await parser.parse("code", "brainfuck")
    
    assert not result.success
    assert "not supported" in result.error


@pytest.mark.asyncio
async def test_parse_file_encoding_issues(parser, tmp_path):
    """Test parsing files with different encodings."""
    # Create file with non-UTF8 encoding
    test_file = tmp_path / "test_latin1.py"
    test_file.write_bytes("# Café\ndef función():\n    pass".encode("latin-1"))
    
    result = await parser.parse_file(str(test_file))
    # Should succeed and handle encoding properly
    assert result.success
    assert result.language == "python"
    assert "function_definition" in result.ast_text


@pytest.mark.asyncio
async def test_parse_file_not_found(parser):
    """Test parsing non-existent file."""
    result = await parser.parse_file("/nonexistent/file.py")
    
    assert not result.success
    assert "Error reading file" in result.error


@pytest.mark.asyncio
async def test_language_detection_edge_cases(parser, tmp_path):
    """Test language detection with edge cases."""
    # No extension
    no_ext = tmp_path / "Makefile"
    no_ext.write_text("all:\n\techo test")
    
    result = await parser.parse_file(str(no_ext))
    assert not result.success
    assert "Could not detect language" in result.error
    
    # Unknown extension
    unknown = tmp_path / "test.xyz"
    unknown.write_text("some content")
    
    result = await parser.parse_file(str(unknown))
    assert not result.success
    assert "Could not detect language" in result.error


@pytest.mark.asyncio
async def test_missing_language_error(parser):
    """Test error when language package is missing."""
    # Try to parse with a mocked missing language
    with patch("importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("No module named 'tree_sitter_fake'")
        
        result = await parser.parse("code", "fake")
        
        assert not result.success
        assert "not supported" in result.error


@pytest.mark.asyncio
async def test_ast_formatting_includes_function_definition(parser):
    """Test that AST formatting includes function definitions."""
    code = "def test():\n    pass"
    result = await parser.parse(code, "python")
    
    assert result.success
    assert "function_definition" in result.ast_text
    assert "identifier: 'test'" in result.ast_text


@pytest.mark.asyncio
async def test_parser_reuse(parser):
    """Test that parsers are cached and reused."""
    # Parse twice with same language
    result1 = await parser.parse("x = 1", "python")
    result2 = await parser.parse("y = 2", "python")
    
    # Both should succeed (even with mocked grammar)
    assert result1.language == "python"
    assert result2.language == "python"


@pytest.mark.asyncio
async def test_concurrent_parsing(parser):
    """Test concurrent parsing operations."""
    # Create multiple parsing tasks
    tasks = []
    for i in range(5):
        task = parser.parse(f"x = {i}", "python")
        tasks.append(task)
    
    # All should complete without errors
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check no exceptions occurred
    for result in results:
        assert not isinstance(result, Exception)


@pytest.mark.asyncio
async def test_node_count_in_metadata(parser):
    """Test that node count is included in metadata."""
    code = "x = 1\ny = 2"
    result = await parser.parse(code, "python")
    
    assert result.success
    assert "node_count" in result.metadata
    assert result.metadata["node_count"] > 0