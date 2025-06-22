"""Tree-sitter based code parser implementation."""

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import tree_sitter

from agenttools.parsers.base import BaseParser, ParseResult
from agenttools.parsers.languages import get_language_config, get_supported_languages
from agenttools.utils import safe_read_file, detect_language_from_file
from agenttools.logging import get_logger

# Set up logger for this module
logger = get_logger("parsers.tree_sitter")

# Pre-load language modules to ensure they're available in subprocesses
_preloaded_modules = {}
for lang in ["python", "javascript", "typescript", "go"]:
    try:
        module_name = f"tree_sitter_{lang}"
        _preloaded_modules[lang] = importlib.import_module(module_name)
        logger.debug(f"Pre-loaded {module_name}")
    except ImportError:
        logger.debug(f"Could not pre-load {module_name}")


class TreeSitterParser(BaseParser):
    """Parser implementation using tree-sitter."""
    
    def __init__(self):
        """Initialize the tree-sitter parser."""
        self.parsers: Dict[str, tree_sitter.Parser] = {}
        self._language_cache: Dict[str, tree_sitter.Language] = {}
    
    async def __aenter__(self):
        """Enter async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        # Cleanup if needed
        pass
    
    def name(self) -> str:
        """Get parser name."""
        return "tree-sitter"
    
    def supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return get_supported_languages()
    
    async def is_language_available(self, language: str) -> bool:
        """Check if language grammar is available."""
        try:
            await self._get_or_install_language(language)
            return True
        except Exception:
            return False
    
    async def parse(self, content: str, language: str) -> ParseResult:
        """Parse source code and return AST."""
        logger.debug(f"Starting parse for language={language}, content_length={len(content)}")
        
        try:
            # Get language configuration
            config = get_language_config(language)
            if not config:
                logger.warning(f"Language {language} not supported")
                return ParseResult(
                    language=language,
                    ast_text="",
                    metadata={"parser": self.name()},
                    error=f"Language {language} not supported"
                )
            
            # Get or install language
            logger.debug(f"Getting or installing language grammar for {language}")
            try:
                lang = await self._get_or_install_language(language)
                logger.debug(f"Successfully loaded language grammar for {language}")
            except Exception as e:
                logger.error(f"Failed to load language grammar for {language}: {e}")
                return ParseResult(
                    language=language,
                    ast_text="",
                    metadata={"parser": self.name()},
                    error=str(e)
                )
            
            # Get or create parser
            if language not in self.parsers:
                logger.debug(f"Creating new parser for {language}")
                parser = tree_sitter.Parser(lang)
                self.parsers[language] = parser
            else:
                logger.debug(f"Reusing existing parser for {language}")
                parser = self.parsers[language]
            
            # Parse the code
            logger.debug("Parsing code with tree-sitter")
            tree = parser.parse(bytes(content, "utf8"))
            logger.debug(f"Parse complete, root node type: {tree.root_node.type}")
            
            # Format AST
            logger.debug("Formatting AST")
            ast_text = self._format_ast(tree.root_node, content, config)
            logger.debug(f"AST formatted, length: {len(ast_text)}")
            
            # Count nodes
            node_count = self._count_nodes(tree.root_node)
            logger.debug(f"Total node count: {node_count}")
            
            return ParseResult(
                language=language,
                ast_text=ast_text,
                metadata={
                    "parser": self.name(),
                    "node_count": node_count,
                    "tree_sitter_version": str(tree_sitter.LANGUAGE_VERSION)
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}", exc_info=True)
            return ParseResult(
                language=language,
                ast_text="",
                metadata={"parser": self.name()},
                error=f"Failed to parse: {str(e)}"
            )
    
    async def parse_file(self, file_path: str, language: Optional[str] = None) -> ParseResult:
        """Parse source file and return AST."""
        # Read file
        try:
            content = safe_read_file(file_path)
        except Exception as e:
            return ParseResult(
                language=language or "unknown",
                ast_text="",
                metadata={"parser": self.name()},
                error=f"Error reading file: {str(e)}"
            )
        
        # Detect language if not provided
        if not language:
            language = detect_language_from_file(file_path)
            if not language:
                return ParseResult(
                    language="unknown",
                    ast_text="",
                    metadata={"parser": self.name()},
                    error="Could not detect language from file extension"
                )
        
        # Parse content
        return await self.parse(content, language)
    
    async def _get_or_install_language(self, language: str) -> tree_sitter.Language:
        """Get language object, installing if necessary."""
        # Check cache first
        if language in self._language_cache:
            return self._language_cache[language]
        
        # Map language names to package names
        package_map = {
            "python": "tree-sitter-python",
            "javascript": "tree-sitter-javascript", 
            "typescript": "tree-sitter-typescript",
            "go": "tree-sitter-go",
            "cpp": "tree-sitter-cpp",
        }
        
        package_name = package_map.get(language)
        if not package_name:
            raise ValueError(f"No package mapping for language: {language}")
        
        # Try to import the language module
        module_name = package_name.replace("-", "_")
        
        # First check if we have it pre-loaded
        if language in _preloaded_modules:
            module = _preloaded_modules[language]
            logger.debug(f"Using pre-loaded module for {language}")
        else:
            try:
                # Try to import existing module
                module = importlib.import_module(module_name)
            except ImportError as e:
                raise RuntimeError(
                    f"Language package {package_name} not installed. "
                    f"Install it with: uv add {package_name} or uv sync --extra languages"
                )
        
        # Get the language object
        # Most tree-sitter language packages expose a language() function that returns a capsule
        if hasattr(module, 'language'):
            capsule = module.language()
            lang = tree_sitter.Language(capsule)
        elif language == "typescript" and hasattr(module, 'language_typescript'):
            # TypeScript module has language_typescript and language_tsx
            capsule = module.language_typescript()
            lang = tree_sitter.Language(capsule)
        else:
            raise RuntimeError(f"Could not find language() function in {module_name}")
        
        # Cache it
        self._language_cache[language] = lang
        return lang
    
    
    def _format_ast(self, node: tree_sitter.Node, source: str, config) -> str:
        """Format AST node as text."""
        lines = []
        self._format_node(node, source, 0, lines, config)
        return "\n".join(lines)
    
    def _format_node(self, node: tree_sitter.Node, source: str, indent: int, lines: List[str], config) -> None:
        """Recursively format AST node."""
        # Format current node
        indent_str = "  " * indent
        
        if logger.isEnabledFor(logging.DEBUG) and indent == 0:
            logger.debug(f"Formatting root AST node type: {node.type}")
        
        # Always show the node type
        if node.child_count == 0:
            # Leaf node - include text
            text = source[node.start_byte:node.end_byte]
            # Escape newlines for display
            text = text.replace("\n", "\\n")
            if len(text) > 50:
                text = text[:47] + "..."
            lines.append(f"{indent_str}{node.type}: {repr(text)}")
        else:
            # Internal node
            lines.append(f"{indent_str}{node.type}")
        
        # Traverse children if not filtered
        if config.node_types_to_include:
            # If we have an include list, only show children for included nodes
            if node.type in config.node_types_to_include:
                for child in node.children:
                    self._format_node(child, source, indent + 1, lines, config)
        elif config.node_types_to_exclude and node.type in config.node_types_to_exclude:
            # Skip children of excluded nodes
            return
        else:
            # No filtering, show all children
            for child in node.children:
                self._format_node(child, source, indent + 1, lines, config)
    
    def _count_nodes(self, node: tree_sitter.Node) -> int:
        """Count total nodes in AST."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count