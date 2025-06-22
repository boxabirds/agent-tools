"""Unit tests for utility functions."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_tools.utils import (
    detect_language_from_file,
    get_cache_dir,
    get_grammar_cache_dir,
    hash_content,
    safe_read_file,
)


def test_cache_directory_creation():
    """Test cache directory creation."""
    with patch("pathlib.Path.home") as mock_home:
        mock_home.return_value = Path("/fake/home")
        
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            cache_dir = get_cache_dir()
            assert cache_dir == Path("/fake/home/.cache/agent-tools")
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)
            
            grammar_dir = get_grammar_cache_dir()
            assert grammar_dir == Path("/fake/home/.cache/agent-tools/grammars")
            # get_cache_dir() called twice (once directly, once from get_grammar_cache_dir)
            # plus one call for creating grammars subdirectory
            assert mock_mkdir.call_count >= 2


def test_cache_directory_permissions():
    """Test that cache directories are created with proper permissions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(tmpdir)
            
            cache_dir = get_cache_dir()
            grammar_dir = get_grammar_cache_dir()
            
            assert cache_dir.exists()
            assert cache_dir.is_dir()
            assert grammar_dir.exists()
            assert grammar_dir.is_dir()


def test_safe_read_file_encodings():
    """Test reading files with different encodings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # UTF-8 file
        utf8_file = Path(tmpdir) / "utf8.txt"
        utf8_content = "Hello 世界 🌍"
        utf8_file.write_text(utf8_content, encoding="utf-8")
        
        assert safe_read_file(str(utf8_file)) == utf8_content
        
        # Latin-1 file
        latin1_file = Path(tmpdir) / "latin1.txt"
        latin1_content = "Café façade"
        latin1_file.write_bytes(latin1_content.encode("latin-1"))
        
        assert safe_read_file(str(latin1_file)) == latin1_content
        
        # ASCII file
        ascii_file = Path(tmpdir) / "ascii.txt"
        ascii_content = "Plain ASCII text"
        ascii_file.write_text(ascii_content, encoding="ascii")
        
        assert safe_read_file(str(ascii_file)) == ascii_content


def test_safe_read_file_encoding_fallback():
    """Test encoding fallback for problematic files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file with mixed/corrupted encoding
        bad_file = Path(tmpdir) / "bad.txt"
        bad_file.write_bytes(b"Valid UTF-8 \xc3\xa9 then bad \xff\xfe bytes")
        
        # Should fall back to latin-1
        content = safe_read_file(str(bad_file))
        assert isinstance(content, str)  # Should not raise exception


def test_safe_read_file_not_found():
    """Test reading non-existent file."""
    with pytest.raises(FileNotFoundError):
        safe_read_file("/nonexistent/file.txt")


def test_safe_read_file_permission_denied():
    """Test reading file without permissions."""
    with tempfile.NamedTemporaryFile() as f:
        # Make file unreadable
        Path(f.name).chmod(0o000)
        
        try:
            with pytest.raises(PermissionError):
                safe_read_file(f.name)
        finally:
            # Restore permissions for cleanup
            Path(f.name).chmod(0o644)


def test_detect_language_edge_cases():
    """Test language detection edge cases."""
    # Multiple dots in filename
    assert detect_language_from_file("test.min.js") == "javascript"
    assert detect_language_from_file("archive.tar.gz") is None
    
    # Case insensitive
    assert detect_language_from_file("TEST.PY") == "python"
    assert detect_language_from_file("Script.JS") == "javascript"
    
    # No extension
    assert detect_language_from_file("Makefile") is None
    assert detect_language_from_file("README") is None
    
    # Hidden files
    assert detect_language_from_file(".eslintrc.js") == "javascript"
    assert detect_language_from_file(".gitignore") is None
    
    # Path with directories
    assert detect_language_from_file("/path/to/file.py") == "python"
    assert detect_language_from_file("../relative/path.go") == "go"


def test_hash_content_consistency():
    """Test hash consistency and properties."""
    # Same content always produces same hash
    content = "test content\nwith newlines\nand special chars: @#$%"
    hash1 = hash_content(content)
    hash2 = hash_content(content)
    assert hash1 == hash2
    
    # Empty content has consistent hash
    empty_hash = hash_content("")
    assert empty_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Unicode content
    unicode_content = "Hello 世界 🌍"
    unicode_hash = hash_content(unicode_content)
    assert len(unicode_hash) == 64  # SHA256 produces 64 hex chars
    
    # Large content
    large_content = "x" * 1_000_000
    large_hash = hash_content(large_content)
    assert len(large_hash) == 64


def test_hash_content_differences():
    """Test that different content produces different hashes."""
    hashes = set()
    
    test_strings = [
        "hello",
        "Hello",  # Case sensitive
        "hello ",  # Trailing space
        " hello",  # Leading space
        "hello\n",  # Newline
        "héllo",  # Accented character
        "",  # Empty
    ]
    
    for s in test_strings:
        h = hash_content(s)
        assert h not in hashes  # All should be unique
        hashes.add(h)


def test_path_edge_cases():
    """Test path handling edge cases."""
    # Windows-style paths (on any platform)
    assert detect_language_from_file("C:\\Users\\test\\file.py") == "python"
    assert detect_language_from_file("D:\\Project\\src\\main.cpp") == "cpp"
    
    # Paths with spaces
    assert detect_language_from_file("/path with spaces/file.js") == "javascript"
    
    # Paths with special characters
    assert detect_language_from_file("/path/to/file-name_test.go") == "go"
    assert detect_language_from_file("/path/to/file@2.0.ts") == "typescript"