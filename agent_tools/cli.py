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
@click.option("--rest", is_flag=True, help="Run RESTful API server instead of MCP stdio server")
@click.option("--host", default="0.0.0.0", help="Host to bind to (REST mode only)")
@click.option("--port", default=8000, type=int, help="Port to bind to (REST mode only)")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), 
              default="INFO", help="Set logging level")
@click.option("--log-file", type=click.Path(), help="Log to specific file")
@click.option("--log-dir", type=click.Path(), default="logs", help="Directory for log files")
def serve(rest: bool, host: str, port: int, log_level: str, log_file: str, log_dir: str):
    """Start the server (MCP stdio by default, RESTful API with --rest flag)."""
    import os
    
    # Set environment variables for logging before importing server
    os.environ["AGENT_TOOLS_LOG_LEVEL"] = log_level
    if log_file:
        os.environ["AGENT_TOOLS_LOG_FILE"] = log_file
    os.environ["AGENT_TOOLS_LOG_DIR"] = log_dir
    
    from agent_tools.mcp.server import run_stdio
    from agent_tools.mcp.rest_server import run_server as run_rest
    
    if rest:
        click.echo(f"Starting RESTful API server on {host}:{port}")
        run_rest(host, port)
    else:
        # MCP stdio mode - no echo to stdout (only stderr)
        import sys
        sys.stderr.write("Starting MCP server (stdio transport)\n")
        run_stdio()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()