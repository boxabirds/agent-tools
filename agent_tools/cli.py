"""Command-line interface for agent-tools."""

import asyncio
import json
import sys
from pathlib import Path

import click

from agent_tools import parse_file, supported_languages


@click.group()
def cli():
    """Agent Tools CLI - AI agent utilities with code parsing."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--language", "-l", help="Override language detection")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def parse(file_path: str, language: str, output: str, format: str):
    """Parse a source code file and output AST."""
    
    async def _parse():
        result = await parse_file(file_path, language)
        
        if format == "json":
            data = {
                "file": file_path,
                "language": result.language,
                "success": result.success,
                "ast": result.ast_text,
                "metadata": result.metadata,
                "error": result.error,
            }
            output_text = json.dumps(data, indent=2)
        else:
            if result.success:
                output_text = f"Language: {result.language}\n"
                output_text += f"File: {file_path}\n"
                output_text += "-" * 40 + "\n"
                output_text += result.ast_text
            else:
                output_text = f"Error parsing file: {result.error}"
        
        if output:
            Path(output).write_text(output_text)
            click.echo(f"Output written to: {output}")
        else:
            click.echo(output_text)
    
    asyncio.run(_parse())


@cli.command()
def languages():
    """List supported programming languages."""
    langs = supported_languages()
    click.echo("Supported languages:")
    for lang in sorted(langs):
        click.echo(f"  - {lang}")


@cli.command()
def serve():
    """Start the MCP server."""
    from agent_tools.mcp.server import main as serve_mcp
    click.echo("Starting MCP server on http://localhost:8000")
    serve_mcp()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()