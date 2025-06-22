"""MCP server implementation for agent-tools."""

import asyncio
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from agent_tools.api import AgentTools
from agent_tools.parsers.base import ParseResult


# Initialize MCP server
mcp = FastMCP("agent-tools")
tools = AgentTools()


class ParseCodeInput(BaseModel):
    """Input for parse_code tool."""
    content: str = Field(..., description="Source code content to parse")
    language: str = Field(..., description="Programming language (e.g., python, javascript)")


class ParseFileInput(BaseModel):
    """Input for parse_file tool."""
    file_path: str = Field(..., description="Path to the source code file")
    language: Optional[str] = Field(None, description="Optional language override")


@mcp.tool()
async def parse_code(input: ParseCodeInput) -> dict:
    """Parse source code and return AST representation.
    
    This tool parses the provided source code using tree-sitter and returns
    a textual representation of the Abstract Syntax Tree (AST).
    """
    result = await tools.parse_code(input.content, input.language)
    
    return {
        "success": result.success,
        "language": result.language,
        "ast": result.ast_text,
        "metadata": result.metadata,
        "error": result.error,
    }


@mcp.tool()
async def parse_file(input: ParseFileInput) -> dict:
    """Parse source code from a file and return AST representation.
    
    This tool reads a source code file and parses it using tree-sitter,
    returning a textual representation of the Abstract Syntax Tree (AST).
    Language is auto-detected from file extension if not provided.
    """
    result = await tools.parse_file(input.file_path, input.language)
    
    return {
        "success": result.success,
        "language": result.language,
        "ast": result.ast_text,
        "metadata": result.metadata,
        "error": result.error,
    }


@mcp.tool()
async def list_supported_languages() -> dict:
    """Get list of supported programming languages.
    
    Returns a list of all programming languages that can be parsed
    by the agent-tools parser.
    """
    languages = tools.supported_languages()
    
    return {
        "languages": languages,
        "count": len(languages),
    }


@mcp.tool()
async def check_language_available(language: str) -> dict:
    """Check if a programming language grammar is available.
    
    This checks whether the grammar for a specific language has been
    downloaded and is ready to use. If not available, it will be
    downloaded on first use.
    """
    available = await tools.is_language_available(language)
    supported = language in tools.supported_languages()
    
    return {
        "language": language,
        "supported": supported,
        "grammar_available": available,
        "message": (
            "Grammar is ready to use" if available else
            "Grammar will be downloaded on first use" if supported else
            "Language is not supported"
        ),
    }


# Resource for providing parser information
@mcp.resource("agent-tools://parsers/info")
async def get_parser_info() -> str:
    """Get information about available parsers."""
    parsers = tools.list_parsers()
    info = f"Available parsers: {', '.join(parsers)}\n"
    info += f"Default parser: tree-sitter\n"
    info += f"Supported languages: {', '.join(tools.supported_languages())}"
    return info


# Health check tool for testing
@mcp.tool()
async def health_check() -> dict:
    """Health check for the agent-tools service."""
    return {"status": "healthy", "service": "agent-tools"}


def main():
    """Run the MCP server."""
    # FastMCP has its own run method
    mcp.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()