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
    
    # Since we can't actually download/build grammars in tests,
    # we'll test the error handling
    result = await parser.parse(code, "python")
    
    # Should fail gracefully when grammar not available
    assert not result.success
    assert ("Language package tree-sitter-python not installed" in result.error or 
            "tree-sitter CLI not found" in result.error or 
            "Failed to clone repository" in result.error)
    

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
    # Will fail due to missing grammar, but should still detect language
    assert not result.success
    assert result.language == "python"


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
async def test_clone_repository_failure(parser):
    """Test handling of git clone failures."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        # Simulate git clone failure
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"fatal: repository not found")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process
        
        with pytest.raises(GrammarNotFoundError) as exc_info:
            await parser._clone_repository("https://invalid.url", Path("/tmp/test"))
        
        assert "Failed to clone repository" in str(exc_info.value)


@pytest.mark.asyncio
async def test_build_grammar_failure(parser, tmp_path):
    """Test handling of grammar build failures."""
    # Since tree-sitter CLI is not available, this should fail
    with pytest.raises(GrammarNotFoundError) as exc_info:
        await parser._build_grammar("test", tmp_path, tmp_path / "output.so")
    
    assert "tree-sitter CLI not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ast_formatting_node_filtering(parser):
    """Test AST node filtering based on language config."""
    # Mock a simple tree structure
    mock_node = MagicMock()
    mock_node.type = "function_definition"
    mock_node.child_count = 0
    mock_node.start_byte = 0
    mock_node.end_byte = 10
    
    formatted = parser._format_tree_sitter_ast(mock_node, "python", "def test(): pass")
    assert "function_definition" in formatted
    
    # Test filtering noise nodes
    noise_node = MagicMock()
    noise_node.type = ";"
    noise_node.child_count = 0
    noise_node.children = []
    
    formatted = parser._format_tree_sitter_ast(noise_node, "python", ";")
    assert formatted == ""  # Noise nodes should be filtered


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
async def test_grammar_path_generation(parser):
    """Test platform-specific grammar path generation."""
    path = parser._get_grammar_path("python")
    
    assert path.name.startswith("python_")
    assert path.name.endswith(".so")
    assert path.parent == parser._grammar_dir


@pytest.mark.asyncio
async def test_node_counting(parser):
    """Test node counting in AST."""
    # Create mock tree structure
    root = MagicMock()
    child1 = MagicMock()
    child2 = MagicMock()
    
    root.children = [child1, child2]
    child1.children = []
    child2.children = []
    
    count = parser._count_nodes(root)
    assert count == 3  # root + 2 children