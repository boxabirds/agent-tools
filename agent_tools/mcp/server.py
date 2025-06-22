"""MCP server implementation for agent-tools."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from agent_tools import parse_code as parse_code_func
from agent_tools import parse_file as parse_file_func
from agent_tools import supported_languages

# Create MCP server
mcp = FastMCP(
    name="agent-tools",
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
    result = await parse_code_func(content, language)
    
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
    result = await parse_file_func(file_path, language)
    
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
    languages = supported_languages()
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
    from agent_tools.api import AgentTools
    from agent_tools.parsers.tree_sitter_parser import TreeSitterParser
    
    tools = AgentTools()
    languages = supported_languages()
    
    supported = language in languages
    
    if supported:
        parser = TreeSitterParser()
        grammar_available = await parser.is_language_available(language)
    else:
        grammar_available = False
    
    return {
        "language": language,
        "supported": supported,
        "grammar_available": grammar_available,
        "message": f"Language {language} is {'supported' if supported else 'not supported'}"
    }


def run_stdio():
    """Run MCP server with stdio transport."""
    # FastMCP handles all the stdio setup internally
    mcp.run(transport="stdio")


def run_http(host: str = "0.0.0.0", port: int = 8000):
    """Run simple HTTP server (non-MCP) for backwards compatibility."""
    from .http_server import run_server
    run_server(host, port)