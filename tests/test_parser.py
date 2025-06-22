"""Unit tests for parser functionality."""

import pytest

from agent_tools.parsers.base import (
    LanguageNotSupportedError,
    ParseResult,
    ParserError,
)
from agent_tools.parsers.languages import (
    get_language_by_extension,
    get_language_config,
    get_supported_languages,
)
from agent_tools.utils import detect_language_from_file, hash_content


def test_parse_result():
    """Test ParseResult dataclass."""
    result = ParseResult(
        language="python",
        ast_text="module",
        metadata={"test": True}
    )
    
    assert result.success is True
    assert result.language == "python"
    assert result.ast_text == "module"
    assert result.error is None
    
    # Test with error
    error_result = ParseResult(
        language="python",
        ast_text="",
        metadata={},
        error="Test error"
    )
    
    assert error_result.success is False
    assert error_result.error == "Test error"


def test_language_detection():
    """Test language detection from file extension."""
    test_cases = [
        ("test.py", "python"),
        ("test.js", "javascript"),
        ("test.jsx", "javascript"),
        ("test.ts", "typescript"),
        ("test.tsx", "typescript"),
        ("test.go", "go"),
        ("test.cpp", "cpp"),
        ("test.cc", "cpp"),
        ("test.h", "c"),
        ("test.hpp", "cpp"),
        ("test.unknown", None),
    ]
    
    for filename, expected in test_cases:
        assert detect_language_from_file(filename) == expected


def test_language_config():
    """Test language configuration."""
    # Test Python config
    python_config = get_language_config("python")
    assert python_config is not None
    assert python_config.name == "python"
    assert python_config.grammar_url.startswith("https://github.com/tree-sitter/")
    assert ".py" in python_config.file_extensions
    
    # Test non-existent language
    assert get_language_config("nonexistent") is None


def test_supported_languages():
    """Test getting supported languages."""
    languages = get_supported_languages()
    
    assert isinstance(languages, list)
    assert len(languages) >= 5
    assert "python" in languages
    assert "javascript" in languages
    assert "typescript" in languages
    assert "go" in languages
    assert "cpp" in languages


def test_get_language_by_extension():
    """Test getting language by file extension."""
    assert get_language_by_extension(".py") == "python"
    assert get_language_by_extension("py") == "python"
    assert get_language_by_extension(".js") == "javascript"
    assert get_language_by_extension(".unknown") is None


def test_hash_content():
    """Test content hashing."""
    content1 = "def hello(): pass"
    content2 = "def hello(): pass"
    content3 = "def goodbye(): pass"
    
    hash1 = hash_content(content1)
    hash2 = hash_content(content2)
    hash3 = hash_content(content3)
    
    # Same content should have same hash
    assert hash1 == hash2
    # Different content should have different hash
    assert hash1 != hash3
    # Hash should be hex string
    assert all(c in "0123456789abcdef" for c in hash1)


def test_parser_exceptions():
    """Test parser exception hierarchy."""
    base_error = ParserError("base error")
    assert isinstance(base_error, Exception)
    
    grammar_error = LanguageNotSupportedError("grammar error")
    assert isinstance(grammar_error, ParserError)
    
    lang_error = LanguageNotSupportedError("language error")
    assert isinstance(lang_error, ParserError)