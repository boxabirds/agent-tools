"""MCP server implementation for mcp-code-parser."""

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from . import parse_code as parse_code_func
from . import parse_file as parse_file_func
from . import supported_languages
from mcp_code_parser.logging import setup_logging, get_logger

# Set up logging
log_level = os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO")
log_file = os.getenv("AGENT_TOOLS_LOG_FILE")
log_dir = os.getenv("AGENT_TOOLS_LOG_DIR", "logs")
logger = setup_logging(log_level, log_file, log_dir)
mcp_logger = get_logger("mcp.server")

# Create MCP server
mcp = FastMCP(
    name="mcp-code-parser",
    version="0.1.0",
    description="Tree-sitter based code parsing tools for AI agents"
)


@mcp.tool()
async def parse_code(content: str, language: str) -> dict:
    """Parse source code and return AST representation.
    
    Args:
        content: Source code content to parse
        language: Programming language (python, javascript, typescript, go, cpp)
        
    Returns:
        Dictionary with parsing results including AST
    """
    mcp_logger.debug(f"parse_code called with language={language}, content_length={len(content)}")
    
    result = await parse_code_func(content, language)
    
    mcp_logger.debug(f"parse_code result: success={result.success}, ast_length={len(result.ast_text) if result.ast_text else 0}")
    if result.error:
        mcp_logger.warning(f"parse_code error: {result.error}")
    
    return {
        "success": result.success,
        "language": result.language,
        "ast": result.ast_text,
        "metadata": result.metadata,
        "error": result.error
    }


@mcp.tool()
async def parse_file(file_path: str, language: Optional[str] = None) -> dict:
    """Parse source code from a file and return AST representation.
    
    Args:
        file_path: Path to the source code file
        language: Optional language override (auto-detected if not provided)
        
    Returns:
        Dictionary with parsing results including AST
    """
    mcp_logger.debug(f"parse_file called with file_path={file_path}, language={language}")
    
    result = await parse_file_func(file_path, language)
    
    mcp_logger.debug(f"parse_file result: success={result.success}, detected_language={result.language}")
    if result.error:
        mcp_logger.warning(f"parse_file error: {result.error}")
    
    return {
        "success": result.success,
        "language": result.language,
        "ast": result.ast_text,
        "metadata": result.metadata,
        "error": result.error
    }


@mcp.tool()
def list_languages() -> dict:
    """List all supported programming languages.
    
    Returns:
        Dictionary with list of supported languages
    """
    mcp_logger.debug("list_languages called")
    
    languages = supported_languages()
    
    mcp_logger.debug(f"list_languages returning {len(languages)} languages")
    
    return {
        "languages": sorted(languages),
        "count": len(languages)
    }


@mcp.tool()
async def check_language(language: str) -> dict:
    """Check if a language is supported and if its grammar is available.
    
    Args:
        language: Language identifier to check
        
    Returns:
        Dictionary with support status and availability
    """
    mcp_logger.debug(f"check_language called with language={language}")
    
    from mcp_code_parser.api import AgentTools
    from .parsers.tree_sitter import TreeSitterParser
    
    tools = AgentTools()
    languages = supported_languages()
    
    supported = language in languages
    
    if supported:
        parser = TreeSitterParser()
        grammar_available = await parser.is_language_available(language)
    else:
        grammar_available = False
    
    mcp_logger.debug(f"check_language result: supported={supported}, grammar_available={grammar_available}")
    
    return {
        "language": language,
        "supported": supported,
        "grammar_available": grammar_available,
        "message": f"Language {language} is {'supported' if supported else 'not supported'}"
    }


def run_stdio():
    """Run MCP server with stdio transport."""
    mcp_logger.info("Starting MCP server in stdio mode")
    mcp_logger.info(f"Log level: {log_level}, Log directory: {log_dir}")
    # FastMCP handles all the stdio setup internally
    mcp.run(transport="stdio")


