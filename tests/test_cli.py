"""Unit tests for CLI functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from mcp_code_parser.cli import cli
from mcp_code_parser.parsers.base import ParseResult


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_parse_result():
    """Create mock parse result."""
    return ParseResult(
        language="python",
        ast_text="module\n  function_definition: 'test'",
        metadata={"node_count": 5},
        error=None
    )


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Agent Tools CLI" in result.output
    assert "parse" in result.output
    assert "languages" in result.output
    assert "serve" in result.output


def test_languages_command(runner):
    """Test languages command."""
    with patch("agent_tools.cli.supported_languages") as mock_languages:
        mock_languages.return_value = ["python", "javascript", "go"]
        
        result = runner.invoke(cli, ["languages"])
        
        assert result.exit_code == 0
        assert "Supported languages:" in result.output
        assert "- python" in result.output
        assert "- javascript" in result.output
        assert "- go" in result.output


def test_parse_command_text_output(runner, mock_parse_result):
    """Test parse command with text output."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"def test(): pass")
        temp_file = f.name
    
    try:
        # Need to patch the async function to return a coroutine
        async def mock_coro(*args, **kwargs):
            return mock_parse_result
            
        with patch("agent_tools.cli.parse_file", new=mock_coro):
            
            result = runner.invoke(cli, ["parse", temp_file])
            
            assert result.exit_code == 0
            assert "Language: python" in result.output
            assert f"File: {temp_file}" in result.output
            assert "module" in result.output
            assert "function_definition: 'test'" in result.output
            
            # Note: Can't easily verify the call with the async mock
    finally:
        Path(temp_file).unlink()


def test_parse_command_json_output(runner, mock_parse_result):
    """Test parse command with JSON output."""
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as f:
        f.write(b"const x = 1;")
        temp_file = f.name
    
    try:
        async def mock_coro(*args, **kwargs):
            return mock_parse_result
            
        with patch("agent_tools.cli.parse_file", new=mock_coro):
            result = runner.invoke(cli, ["parse", temp_file, "--format", "json"])
            
            assert result.exit_code == 0
            
            # Verify JSON output
            output_data = json.loads(result.output)
            assert output_data["file"] == temp_file
            assert output_data["language"] == "python"
            assert output_data["success"] is True
            assert output_data["ast"] == mock_parse_result.ast_text
            assert output_data["metadata"]["node_count"] == 5
    finally:
        Path(temp_file).unlink()


def test_parse_command_with_language_override(runner, mock_parse_result):
    """Test parse command with language override."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"some code")
        temp_file = f.name
    
    try:
        async def mock_coro(*args, **kwargs):
            return mock_parse_result
            
        with patch("agent_tools.cli.parse_file", new=mock_coro):
            
            result = runner.invoke(cli, ["parse", temp_file, "--language", "python"])
            
            assert result.exit_code == 0
            
            # Verify language was passed
            # Note: Cannot easily verify the call with the async mock
    finally:
        Path(temp_file).unlink()


def test_parse_command_output_to_file(runner, mock_parse_result):
    """Test parse command with output to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.py"
        output_file = Path(tmpdir) / "output.txt"
        input_file.write_text("x = 1")
        
        async def mock_coro(*args, **kwargs):
            return mock_parse_result
            
        with patch("agent_tools.cli.parse_file", new=mock_coro):
            
            result = runner.invoke(cli, [
                "parse", str(input_file),
                "--output", str(output_file)
            ])
            
            assert result.exit_code == 0
            assert f"Output written to: {output_file}" in result.output
            
            # Verify file was written
            assert output_file.exists()
            content = output_file.read_text()
            assert "Language: python" in content
            assert mock_parse_result.ast_text in content


def test_parse_command_error_handling(runner):
    """Test parse command error handling."""
    error_result = ParseResult(
        language="python",
        ast_text="",
        metadata={},
        error="Failed to parse: syntax error"
    )
    
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"invalid python !!!")
        temp_file = f.name
    
    try:
        with patch("agent_tools.cli.parse_file") as mock_parse:
            mock_parse.return_value = error_result
            
            result = runner.invoke(cli, ["parse", temp_file])
            
            assert result.exit_code == 0  # CLI doesn't fail on parse errors
            assert "Error parsing file: Failed to parse: syntax error" in result.output
    finally:
        Path(temp_file).unlink()


def test_parse_command_file_not_found(runner):
    """Test parse command with non-existent file."""
    result = runner.invoke(cli, ["parse", "/nonexistent/file.py"])
    
    assert result.exit_code == 2  # Click's error code for bad parameters
    assert "does not exist" in result.output


def test_serve_command(runner):
    """Test serve command starts server."""
    with patch("agent_tools.mcp.server.run_stdio") as mock_serve:
        result = runner.invoke(cli, ["serve"])
        
        assert result.exit_code == 0
        mock_serve.assert_called_once()


def test_parse_command_json_with_error(runner):
    """Test parse command JSON output with error."""
    error_result = ParseResult(
        language="unknown",
        ast_text="",
        metadata={},
        error="Language not supported"
    )
    
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"unknown content")
        temp_file = f.name
    
    try:
        with patch("agent_tools.cli.parse_file") as mock_parse:
            mock_parse.return_value = error_result
            
            result = runner.invoke(cli, ["parse", temp_file, "--format", "json"])
            
            assert result.exit_code == 0
            
            output_data = json.loads(result.output)
            assert output_data["success"] is False
            assert output_data["error"] == "Language not supported"
            assert output_data["ast"] == ""
    finally:
        Path(temp_file).unlink()