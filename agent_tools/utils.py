"""Common utilities for agent-tools."""

import hashlib
import os
from pathlib import Path
from typing import Optional


def get_cache_dir() -> Path:
    """Get or create cache directory for agent-tools."""
    cache_dir = Path.home() / ".cache" / "agent-tools"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_grammar_cache_dir() -> Path:
    """Get or create grammar cache directory."""
    grammar_dir = get_cache_dir() / "grammars"
    grammar_dir.mkdir(parents=True, exist_ok=True)
    return grammar_dir


def detect_language_from_file(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".c": "c",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".hxx": "cpp",
    }
    
    ext = Path(file_path).suffix.lower()
    return ext_to_lang.get(ext)


def hash_content(content: str) -> str:
    """Generate hash of content for caching."""
    return hashlib.sha256(content.encode()).hexdigest()


def safe_read_file(file_path: str, encoding: str = "utf-8") -> str:
    """Safely read file content."""
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for enc in ["latin-1", "ascii", "utf-16"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise