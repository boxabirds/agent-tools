"""Tree-sitter based code parser with dynamic grammar loading."""

import asyncio
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

import httpx
import tree_sitter

from agent_tools.parsers.base import (
    BaseParser,
    GrammarNotFoundError,
    LanguageNotSupportedError,
    ParseError,
    ParseResult,
)
from agent_tools.parsers.languages import get_language_config, get_supported_languages
from agent_tools.utils import (
    detect_language_from_file,
    get_grammar_cache_dir,
    hash_content,
    safe_read_file,
)


class TreeSitterParser(BaseParser):
    """Tree-sitter based parser with dynamic grammar loading."""
    
    def __init__(self):
        self._languages: Dict[str, tree_sitter.Language] = {}
        self._parsers: Dict[str, tree_sitter.Parser] = {}
        self._grammar_dir = get_grammar_cache_dir()
        self._http_client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()
    
    async def parse(self, content: str, language: str) -> ParseResult:
        """Parse code content and return AST representation."""
        try:
            # Ensure language is supported
            if language not in self.supported_languages():
                raise LanguageNotSupportedError(f"Language '{language}' is not supported")
            
            # Ensure grammar is available
            if not await self.is_language_available(language):
                await self._download_and_build_grammar(language)
            
            # Get or create parser
            parser = await self._get_parser(language)
            
            # Parse the content
            tree = parser.parse(bytes(content, "utf8"))
            
            # Format AST to text
            ast_text = self._format_tree_sitter_ast(tree.root_node, language, content)
            
            return ParseResult(
                language=language,
                ast_text=ast_text,
                metadata={
                    "parser": "tree-sitter",
                    "content_hash": hash_content(content),
                    "node_count": self._count_nodes(tree.root_node),
                }
            )
            
        except Exception as e:
            return ParseResult(
                language=language,
                ast_text="",
                metadata={"parser": "tree-sitter"},
                error=str(e)
            )
    
    async def parse_file(self, file_path: str, language: Optional[str] = None) -> ParseResult:
        """Parse code from file."""
        # Auto-detect language if not provided
        if language is None:
            language = detect_language_from_file(file_path)
            if language is None:
                return ParseResult(
                    language="unknown",
                    ast_text="",
                    metadata={"file_path": file_path},
                    error=f"Could not detect language for file: {file_path}"
                )
        
        # Read file content
        try:
            content = safe_read_file(file_path)
        except Exception as e:
            return ParseResult(
                language=language,
                ast_text="",
                metadata={"file_path": file_path},
                error=f"Error reading file: {str(e)}"
            )
        
        # Parse content
        result = await self.parse(content, language)
        result.metadata["file_path"] = file_path
        return result
    
    def supported_languages(self) -> List[str]:
        """Return list of supported language identifiers."""
        return get_supported_languages()
    
    async def is_language_available(self, language: str) -> bool:
        """Check if language grammar is available/downloaded."""
        grammar_path = self._get_grammar_path(language)
        return grammar_path.exists()
    
    def _get_grammar_path(self, language: str) -> Path:
        """Get path to compiled grammar file."""
        system = platform.system().lower()
        arch = platform.machine().lower()
        return self._grammar_dir / f"{language}_{system}_{arch}.so"
    
    async def _get_parser(self, language: str) -> tree_sitter.Parser:
        """Get or create parser for language."""
        if language not in self._parsers:
            # Load language
            if language not in self._languages:
                grammar_path = self._get_grammar_path(language)
                self._languages[language] = tree_sitter.Language(str(grammar_path), language)
            
            # Create parser
            parser = tree_sitter.Parser()
            parser.set_language(self._languages[language])
            self._parsers[language] = parser
            
        return self._parsers[language]
    
    async def _download_and_build_grammar(self, language: str) -> None:
        """Download and build tree-sitter grammar."""
        config = get_language_config(language)
        if not config:
            raise LanguageNotSupportedError(f"No configuration for language: {language}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download grammar repository
            repo_path = temp_path / config.repo_name
            await self._clone_repository(config.grammar_url, repo_path)
            
            # Build grammar
            grammar_path = self._get_grammar_path(language)
            await self._build_grammar(language, repo_path, grammar_path)
    
    async def _clone_repository(self, repo_url: str, target_path: Path) -> None:
        """Clone grammar repository."""
        # Use git to clone (subprocess)
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", repo_url, str(target_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise GrammarNotFoundError(
                f"Failed to clone repository: {stderr.decode()}"
            )
    
    async def _build_grammar(self, language: str, repo_path: Path, output_path: Path) -> None:
        """Build tree-sitter grammar."""
        # In newer tree-sitter versions, grammars need to be built differently
        # For now, we'll skip the actual building and assume pre-built binaries
        # This is a limitation we need to document
        import platform
        import shutil
        
        # Look for pre-built binary
        system = platform.system().lower()
        possible_names = [
            f"tree-sitter-{language}.so",
            f"libtree-sitter-{language}.so", 
            f"tree-sitter-{language}.dylib",
            f"libtree-sitter-{language}.dylib",
            f"tree-sitter-{language}.dll"
        ]
        
        binary_found = False
        for name in possible_names:
            binary_path = repo_path / name
            if binary_path.exists():
                shutil.copy(binary_path, output_path)
                binary_found = True
                break
                
        if not binary_found:
            # Try to build using subprocess
            try:
                # This would require tree-sitter CLI to be installed
                proc = await asyncio.create_subprocess_exec(
                    "tree-sitter", "build", "--output", str(output_path),
                    cwd=str(repo_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise Exception(f"Build failed: {stderr.decode()}")
            except FileNotFoundError:
                raise GrammarNotFoundError(
                    "tree-sitter CLI not found. Please install it to build grammars."
                )
    
    def _format_tree_sitter_ast(
        self, node: tree_sitter.Node, language: str, source: str
    ) -> str:
        """Format tree-sitter AST node as text."""
        config = get_language_config(language)
        lines = []
        
        def should_include_node(node_type: str) -> bool:
            if config and config.node_types_to_include:
                return node_type in config.node_types_to_include
            if config and config.node_types_to_exclude:
                return node_type not in config.node_types_to_exclude
            # Default: include all except common noise
            noise_types = {"comment", "line_comment", "block_comment", ";", ",", "(", ")", "{", "}"}
            return node_type not in noise_types
        
        def format_node(node: tree_sitter.Node, indent: int = 0) -> None:
            indent_str = "  " * indent
            
            # Skip nodes we don't want
            if not should_include_node(node.type):
                # Still process children
                for child in node.children:
                    format_node(child, indent)
                return
            
            # Format node
            if node.child_count == 0:
                # Leaf node - include text
                text = source[node.start_byte:node.end_byte].strip()
                if text:
                    lines.append(f"{indent_str}{node.type}: {repr(text)}")
                else:
                    lines.append(f"{indent_str}{node.type}")
            else:
                # Non-leaf node
                lines.append(f"{indent_str}{node.type}")
                for child in node.children:
                    format_node(child, indent + 1)
        
        format_node(node)
        return "\n".join(lines)
    
    def _count_nodes(self, node: tree_sitter.Node) -> int:
        """Count total nodes in tree."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count