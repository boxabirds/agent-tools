"""Integration tests for mcp-code-parser parser."""

import asyncio
from pathlib import Path

import pytest

from mcp_code_parser import parse_file, supported_languages


@pytest.fixture
def samples_dir():
    """Get samples directory."""
    return Path(__file__).parent / "samples"


@pytest.mark.asyncio
async def test_parse_python_complex(samples_dir):
    """Test parsing complex Python file."""
    file_path = samples_dir / "python_complex.py"
    result = await parse_file(str(file_path))
    
    assert result.success is True
    assert result.language == "python"
    assert "class" in result.ast_text
    assert result.error is None


@pytest.mark.asyncio
async def test_parse_javascript_complex(samples_dir):
    """Test parsing complex JavaScript file."""
    file_path = samples_dir / "javascript_complex.js"
    result = await parse_file(str(file_path))
    
    assert result.success is True
    assert result.language == "javascript"
    assert "function" in result.ast_text or "class" in result.ast_text
    assert result.error is None


@pytest.mark.asyncio
async def test_parse_typescript_complex(samples_dir):
    """Test parsing complex TypeScript file."""
    file_path = samples_dir / "typescript_complex.ts"
    result = await parse_file(str(file_path))
    
    assert result.success is True
    assert result.language == "typescript"
    assert "class" in result.ast_text or "interface" in result.ast_text
    assert result.error is None


@pytest.mark.asyncio
async def test_parse_go_complex(samples_dir):
    """Test parsing complex Go file."""
    file_path = samples_dir / "go_complex.go"
    result = await parse_file(str(file_path))
    
    assert result.success is True
    assert result.language == "go"
    assert "func" in result.ast_text or "package" in result.ast_text
    assert result.error is None


@pytest.mark.asyncio
async def test_parse_cpp_complex(samples_dir):
    """Test parsing complex C++ file."""
    file_path = samples_dir / "cpp_complex.cpp"
    result = await parse_file(str(file_path))
    
    assert result.success is True
    assert result.language == "cpp"
    assert "class" in result.ast_text or "function" in result.ast_text
    assert result.error is None


@pytest.mark.asyncio
async def test_auto_language_detection(samples_dir):
    """Test automatic language detection from file extension."""
    test_files = [
        ("python_complex.py", "python"),
        ("javascript_complex.js", "javascript"),
        ("typescript_complex.ts", "typescript"),
        ("go_complex.go", "go"),
        ("cpp_complex.cpp", "cpp"),
    ]
    
    for filename, expected_lang in test_files:
        file_path = samples_dir / filename
        result = await parse_file(str(file_path))  # No language specified
        assert result.language == expected_lang
        assert result.success is True


@pytest.mark.asyncio
async def test_parse_nonexistent_file():
    """Test parsing non-existent file."""
    result = await parse_file("/path/to/nonexistent/file.py")
    
    assert not result.success
    assert result.error is not None
    assert "Error reading file" in result.error


@pytest.mark.asyncio
async def test_supported_languages():
    """Test getting supported languages."""
    languages = supported_languages()
    
    assert isinstance(languages, list)
    assert len(languages) >= 5
    assert "python" in languages
    assert "javascript" in languages
    assert "typescript" in languages
    assert "go" in languages
    assert "cpp" in languages


@pytest.mark.asyncio
async def test_parse_small_code_snippets():
    """Test parsing small code snippets."""
    snippets = [
        ("python", "def hello(): return 'world'"),
        ("javascript", "const add = (a, b) => a + b;"),
        ("go", "func main() { fmt.Println(\"Hello\") }"),
    ]
    
    for lang, code in snippets:
        from mcp_code_parser import parse_code
        result = await parse_code(code, lang)
        
        assert result.success is True
        assert result.language == lang
        assert result.error is None
        assert len(result.ast_text) > 0