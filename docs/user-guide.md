# MCP Code Parser User Guide

This guide walks you through using agent-tools' code parsing functionality in three different ways:
1. [Direct Python API](#python-api-usage)
2. [RESTful API](#restful-api-usage)
3. [Model Context Protocol (MCP)](#mcp-usage)

## Table of Contents

- [Installation](#installation)
- [Python API Usage](#python-api-usage)
  - [Basic Parsing](#basic-parsing)
  - [File Parsing](#file-parsing)
  - [Error Handling](#error-handling)
  - [Advanced Usage](#advanced-usage)
- [RESTful API Usage](#restful-api-usage)
  - [Starting the Server](#starting-the-rest-server)
  - [API Endpoints](#api-endpoints)
  - [Creating Analyses](#creating-analyses)
  - [Retrieving Results](#retrieving-results)
  - [Error Responses](#error-responses)
- [MCP Usage](#mcp-usage)
  - [Server Configuration](#mcp-server-configuration)
  - [Using with Claude Desktop](#claude-desktop-integration)
  - [Using with Other MCP Clients](#other-mcp-clients)
  - [Available Tools](#available-mcp-tools)
- [Language Support](#language-support)
- [Understanding AST Output](#understanding-ast-output)
- [Troubleshooting](#troubleshooting)

## Installation

First, install agent-tools using uv (recommended) or pip:

```bash
# Using uv (recommended)
git clone https://github.com/yourusername/agent-tools.git
cd agent-tools
uv sync

# Using pip
pip install agent-tools
```

## Python API Usage

The Python API provides direct access to the parsing functionality through async functions.

### Basic Parsing

Parse code directly by providing the source code and language:

```python
import asyncio
from agent_tools import parse_code

async def main():
    # Parse Python code
    result = await parse_code(
        content="def greet(name):\n    return f'Hello, {name}!'",
        language="python"
    )
    
    if result.success:
        print("AST:")
        print(result.ast_text)
        print(f"\nMetadata: {result.metadata}")
    else:
        print(f"Error: {result.error}")

asyncio.run(main())
```

Output:
```
AST:
module
  function_definition
    identifier: 'greet'
    parameters
      identifier: 'name'
    block
      return_statement
        string: "f'Hello, {name}!'"

Metadata: {'parser': 'tree-sitter', 'node_count': 9}
```

### File Parsing

Parse code from files with automatic language detection:

```python
import asyncio
from agent_tools import parse_file

async def main():
    # Parse a file (language auto-detected from extension)
    result = await parse_file("src/main.py")
    
    print(f"Detected language: {result.language}")
    print(f"Success: {result.success}")
    
    if result.success:
        # The AST can be quite large, so maybe just show statistics
        lines = result.ast_text.split('\n')
        print(f"AST lines: {len(lines)}")
        print(f"Top-level nodes: {len([l for l in lines if not l.startswith(' ')])}")

asyncio.run(main())
```

You can also specify the language explicitly:

```python
# Force parsing as JavaScript even if file extension suggests otherwise
result = await parse_file("config.json", language="javascript")
```

### Error Handling

The parser handles errors gracefully and provides informative error messages:

```python
import asyncio
from agent_tools import parse_code, parse_file

async def main():
    # Example 1: Unsupported language
    result = await parse_code("SELECT * FROM users", "sql")
    if not result.success:
        print(f"Error: {result.error}")
        # Output: Error: No package mapping for language: sql
    
    # Example 2: File not found
    result = await parse_file("nonexistent.py")
    if not result.success:
        print(f"Error: {result.error}")
        # Output: Error: Error reading file: [Errno 2] No such file or directory: 'nonexistent.py'
    
    # Example 3: Invalid syntax (tree-sitter still parses it)
    result = await parse_code("def broken syntax", "python")
    if result.success:
        print("Tree-sitter can parse incomplete code!")
        print(result.ast_text)
        # Tree-sitter is forgiving and will parse partial/invalid syntax

asyncio.run(main())
```

### Advanced Usage

#### Batch Processing

Process multiple files concurrently:

```python
import asyncio
from pathlib import Path
from agent_tools import parse_file

async def analyze_codebase(directory: Path):
    """Analyze all Python files in a directory."""
    py_files = list(directory.rglob("*.py"))
    
    # Parse all files concurrently
    tasks = [parse_file(str(f)) for f in py_files]
    results = await asyncio.gather(*tasks)
    
    # Analyze results
    successful = sum(1 for r in results if r.success)
    total_nodes = sum(r.metadata.get('node_count', 0) for r in results if r.success)
    
    print(f"Parsed {successful}/{len(py_files)} files successfully")
    print(f"Total AST nodes: {total_nodes}")
    
    # Find files with classes
    for file, result in zip(py_files, results):
        if result.success and "class_definition" in result.ast_text:
            print(f"  {file.name} contains classes")

asyncio.run(analyze_codebase(Path("./src")))
```

#### Custom Processing

Extract specific information from the AST:

```python
import asyncio
from agent_tools import parse_code

def extract_functions(ast_text: str) -> list[str]:
    """Extract function names from AST."""
    functions = []
    lines = ast_text.split('\n')
    
    for i, line in enumerate(lines):
        if 'function_definition' in line:
            # Look for the identifier on the next line
            for j in range(i + 1, min(i + 5, len(lines))):
                if 'identifier:' in lines[j]:
                    func_name = lines[j].split("'")[1]
                    functions.append(func_name)
                    break
    
    return functions

async def main():
    code = """
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

class Calculator:
    def divide(self, a, b):
        return a / b
"""
    
    result = await parse_code(code, "python")
    if result.success:
        functions = extract_functions(result.ast_text)
        print(f"Found functions: {functions}")
        # Output: Found functions: ['add', 'multiply', 'divide']

asyncio.run(main())
```

## RESTful API Usage

The RESTful API provides HTTP endpoints for code parsing, following REST principles and JSON:API specification.

### Starting the REST Server

Start the REST server using the CLI:

```bash
# Start with default settings (port 8000)
uv run agent-tools serve --rest

# Start on a specific port and host
uv run agent-tools serve --rest --host 0.0.0.0 --port 8080

# Start with debug logging
uv run agent-tools serve --rest --log-level DEBUG
```

### API Endpoints

The REST API provides the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and links |
| `/languages` | GET | List all supported languages |
| `/languages/{id}` | GET | Get details about a specific language |
| `/parsers` | GET | List available parsers |
| `/analyses` | POST | Create a new code analysis |
| `/analyses/{id}` | GET | Retrieve an analysis result |
| `/openapi.yaml` | GET | OpenAPI specification |

### Creating Analyses

#### Parse Code Content

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "source": {
      "content": "function greet(name) {\n  return `Hello, ${name}!`;\n}",
      "language": "javascript"
    }
  }'
```

Response:
```json
{
  "data": {
    "type": "analysis",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "attributes": {
      "language": "javascript",
      "parser": "tree-sitter",
      "success": true,
      "ast": "program\n  function_declaration\n    identifier: 'greet'\n    formal_parameters\n      identifier: 'name'\n    statement_block\n      return_statement\n        template_string\n          string: '`Hello, ${name}!`'",
      "error": null,
      "metadata": {
        "parser": "tree-sitter",
        "node_count": 15
      },
      "created_at": "2024-01-01T12:00:00Z"
    },
    "relationships": {
      "language": {
        "data": {"type": "language", "id": "javascript"}
      },
      "parser": {
        "data": {"type": "parser", "id": "tree-sitter"}
      }
    },
    "links": {
      "self": "/analyses/550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

#### Parse File

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "source": {
      "file_path": "/path/to/your/file.py"
    }
  }'
```

The language will be auto-detected from the file extension. You can override it:

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "source": {
      "file_path": "/path/to/your/file",
      "language": "python"
    }
  }'
```

### Retrieving Results

Get a previously created analysis:

```bash
curl http://localhost:8000/analyses/550e8400-e29b-41d4-a716-446655440000
```

### Error Responses

The API returns appropriate HTTP status codes and error messages:

#### 400 Bad Request
```json
{
  "errors": [{
    "status": "400",
    "title": "Bad Request",
    "detail": "Language is required when parsing content"
  }]
}
```

#### 404 Not Found
```json
{
  "errors": [{
    "status": "404",
    "title": "Not Found",
    "detail": "Analysis 123e4567-e89b-12d3-a456-426614174000 not found"
  }]
}
```

### Example: Python Client

Here's a simple Python client for the REST API:

```python
import httpx
import asyncio

class AgentToolsClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def parse_code(self, content: str, language: str) -> dict:
        """Parse code and return the analysis."""
        response = await self.client.post(
            f"{self.base_url}/analyses",
            json={
                "source": {
                    "content": content,
                    "language": language
                }
            },
            headers={"Content-Type": "application/vnd.api+json"}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_analysis(self, analysis_id: str) -> dict:
        """Retrieve a previous analysis."""
        response = await self.client.get(
            f"{self.base_url}/analyses/{analysis_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def list_languages(self) -> dict:
        """List all supported languages."""
        response = await self.client.get(f"{self.base_url}/languages")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()

# Usage example
async def main():
    client = AgentToolsClient()
    
    # Parse some code
    result = await client.parse_code(
        "print('Hello, World!')",
        "python"
    )
    
    if result["data"]["attributes"]["success"]:
        print("AST:", result["data"]["attributes"]["ast"])
    
    # List languages
    languages = await client.list_languages()
    for lang in languages["data"]:
        print(f"- {lang['id']}: {lang['attributes']['name']}")
    
    await client.close()

asyncio.run(main())
```

## MCP Usage

The Model Context Protocol (MCP) allows AI assistants like Claude Desktop to use agent-tools directly.

### MCP Server Configuration

The MCP server runs using stdio transport (standard input/output) and exposes tools that AI assistants can call.

### Claude Desktop Integration

Add agent-tools to your Claude Desktop configuration:

1. Open the configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the agent-tools server:

```json
{
  "mcpServers": {
    "agent-tools": {
      "command": "uv",
      "args": ["run", "agent-tools", "serve"],
      "cwd": "/path/to/agent-tools"
    }
  }
}
```

3. Restart Claude Desktop

4. You can now ask Claude to parse code for you:
   - "Parse this Python file: /path/to/file.py"
   - "Show me the AST structure of this JavaScript code: ..."
   - "What languages does agent-tools support?"

### Other MCP Clients

#### Cursor

Config location: `~/.cursor/mcp/servers.json`

```json
{
  "mcpServers": {
    "agent-tools": {
      "command": "uv",
      "args": ["run", "agent-tools", "serve"],
      "cwd": "/path/to/agent-tools"
    }
  }
}
```

#### Windsurf

Config location: 
- macOS: `~/Library/Application Support/windsurf/mcp/servers.json`
- Windows: `%APPDATA%\windsurf\mcp\servers.json`

Use the same configuration as above.

### Available MCP Tools

The MCP server exposes four tools:

#### 1. parse_code
Parse source code and return AST representation.

**Parameters:**
- `content` (string, required): Source code to parse
- `language` (string, required): Programming language

**Example:**
```json
{
  "tool": "parse_code",
  "arguments": {
    "content": "def hello():\n    return 'world'",
    "language": "python"
  }
}
```

#### 2. parse_file
Parse source code from a file.

**Parameters:**
- `file_path` (string, required): Path to the source file
- `language` (string, optional): Language override (auto-detected if not provided)

**Example:**
```json
{
  "tool": "parse_file",
  "arguments": {
    "file_path": "/Users/me/project/main.py"
  }
}
```

#### 3. list_languages
List all supported programming languages.

**Parameters:** None

**Example:**
```json
{
  "tool": "list_languages",
  "arguments": {}
}
```

#### 4. check_language
Check if a language is supported and available.

**Parameters:**
- `language` (string, required): Language identifier to check

**Example:**
```json
{
  "tool": "check_language",
  "arguments": {
    "language": "rust"
  }
}
```

### MCP Debugging

Enable debug logging to troubleshoot MCP issues:

```json
{
  "mcpServers": {
    "agent-tools": {
      "command": "uv",
      "args": ["run", "agent-tools", "serve", "--log-level", "DEBUG"],
      "cwd": "/path/to/agent-tools"
    }
  }
}
```

Logs are saved to:
- Default: `logs/agent_tools_YYYYMMDD_HHMMSS.log`
- Claude Desktop logs: `~/Library/Logs/Claude/mcp-server-agent-tools.log` (macOS)

## Language Support

### Pre-installed Languages

The following languages are pre-installed and ready to use:

| Language | File Extensions | Identifier |
|----------|----------------|------------|
| Python | `.py`, `.pyw` | `python` |
| JavaScript | `.js`, `.jsx`, `.mjs` | `javascript` |
| TypeScript | `.ts`, `.tsx` | `typescript` |
| Go | `.go` | `go` |

### Optional Languages

Additional languages can be installed:

| Language | Installation | Identifier |
|----------|-------------|------------|
| C++ | `uv sync --extra cpp` | `cpp` |

### Checking Language Support

#### Python API
```python
from agent_tools import supported_languages

# Get list of supported languages
languages = supported_languages()
print(languages)  # ['python', 'javascript', 'typescript', 'go', 'cpp']
```

#### REST API
```bash
# List all languages
curl http://localhost:8000/languages

# Check specific language
curl http://localhost:8000/languages/python
```

#### MCP
Ask the AI assistant: "What languages does agent-tools support?"

## Understanding AST Output

The Abstract Syntax Tree (AST) output shows the hierarchical structure of your code:

```
module                          # Root node for Python files
  function_definition           # Function declaration
    identifier: 'hello'         # Function name
    parameters                  # Parameter list
      identifier: 'name'        # Parameter name
    block                       # Function body
      return_statement          # Return statement
        string: "'world'"       # String literal
```

### Key Concepts

1. **Indentation** indicates hierarchy - child nodes are indented under parents
2. **Node types** (like `function_definition`) describe the syntactic element
3. **Leaf nodes** show actual code content (like `identifier: 'hello'`)
4. **Filtering** - agent-tools filters out pure syntax tokens (like `:`, `(`, `)`) to focus on meaningful structure

### Using AST for Analysis

The AST can be used for various code analysis tasks:

- **Finding specific constructs**: Search for `class_definition`, `function_definition`, etc.
- **Counting code elements**: Count functions, classes, imports
- **Detecting patterns**: Find recursive calls, nested loops, etc.
- **Code metrics**: Calculate complexity based on nesting depth

## Troubleshooting

### Common Issues

#### "Language package not installed" error

**Problem**: Getting errors like "Language package tree-sitter-python not installed"

**Solutions**:
1. Make sure you're running commands with `uv run`:
   ```bash
   uv run agent-tools parse example.py  # ✓ Correct
   agent-tools parse example.py         # ✗ Wrong
   ```

2. Reinstall dependencies:
   ```bash
   uv sync
   ```

3. Check installation:
   ```bash
   uv pip list | grep tree-sitter
   ```

#### MCP server not connecting

**Problem**: Claude Desktop shows "Failed to connect to agent-tools"

**Solutions**:
1. Verify the path in config is correct
2. Test the server manually:
   ```bash
   cd /path/to/agent-tools
   uv run agent-tools serve
   ```
3. Check logs in `~/Library/Logs/Claude/mcp-server-agent-tools.log`

#### REST API connection refused

**Problem**: `curl: (7) Failed to connect to localhost port 8000`

**Solutions**:
1. Make sure the server is running:
   ```bash
   uv run agent-tools serve --rest
   ```
2. Check if port is already in use:
   ```bash
   lsof -i :8000
   ```
3. Try a different port:
   ```bash
   uv run agent-tools serve --rest --port 8080
   ```

### Debug Mode

Enable debug logging for detailed information:

```bash
# For direct usage
LOG_LEVEL=DEBUG uv run python your_script.py

# For REST server
uv run agent-tools serve --rest --log-level DEBUG

# For MCP server
uv run agent-tools serve --log-level DEBUG
```

### Getting Help

- Check the [README](../README.md) for installation instructions
- See [Technical Design](tech-design.md) for architecture details
- Review [MCP vs REST](mcp-vs-rest.md) for protocol comparison
- Report issues at: https://github.com/yourusername/agent-tools/issues