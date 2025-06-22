# mcp-code-parser

An opinionated MCP wrapper for tree-sitter that provides structured code parsing for AI agents. It exposes tree-sitter's powerful parsing capabilities through the Model Context Protocol, making it accessible to Claude Desktop, Cursor, Windsurf, and other MCP clients.

## Why mcp-code-parser?

### Why Parse Code Instead of Sending Raw Source?

Sending raw source code to LLMs has significant limitations:

1. **Context Window Efficiency**: A 1,000-line file might have only 50 lines relevant to your query. Parsing lets you extract just the function signatures, class structures, or specific constructs you need.

2. **Structured Understanding**: LLMs work better with structured data. An AST shows relationships explicitly (which class contains which methods, scope boundaries, etc.) rather than relying on the LLM to infer structure from indentation and syntax.

3. **Cross-Language Consistency**: Different languages express the same concepts differently. ASTs normalize these into consistent structures, making it easier to work across languages.

4. **Precise Navigation**: You can query specific parts of code ("show me all error handlers" or "find recursive functions") without regex gymnastics or hoping the LLM notices patterns.

5. **Token Economy**: AST representations are more compact than full source code while preserving all structural information. This means more effective use of context windows and lower API costs.

### Value Beyond Tree-sitter

While tree-sitter is an excellent parsing library, mcp-code-parser adds significant value for AI workflows:

### 1. **MCP Protocol Integration**
The primary value is exposing tree-sitter's capabilities through the Model Context Protocol (MCP), making it accessible to MCP clients like Claude Desktop, Cursor, and Windsurf. Without this, these tools cannot use tree-sitter for code analysis.

### 2. **Intelligent AST Filtering**
Raw tree-sitter output includes every syntactic element (parentheses, colons, keywords). MCP Code Parser filters this noise to show only semantically meaningful nodes:
- Functions, classes, and methods
- Control flow structures
- Important expressions
- Actual code snippets in leaf nodes

This makes the AST actually useful for MCP clients that need to understand code structure without drowning in syntax.

**Example: Python function parsing**

Raw tree-sitter output:
```
function_definition
  def: 'def'
  identifier: 'hello'
  parameters
    (: '('
    identifier: 'name'
    ): ')'
  :: ':'
  block
    return_statement
      return: 'return'
      binary_operator
        string: '"Hello, "'
        +: '+'
        identifier: 'name'
```

MCP Code Parser filtered output:
```
function_definition
  identifier: 'hello'
  parameters
    identifier: 'name'
  block
    return_statement
      binary_operator
        string: '"Hello, "'
        identifier: 'name'
```

### 3. **Production-Ready Infrastructure**
- Automatic file encoding detection (UTF-8, Latin-1, ASCII, UTF-16)
- Pre-packaged language grammars (no manual installation)
- Structured error handling with consistent results
- Comprehensive async/await support
- Proper logging and debugging tools

### 4. **Extensible Architecture**
The `BaseParser` abstraction allows adding other parsing backends (LSP, semantic analysis) without changing the API, making it future-proof for evolving AI needs.

## Features

- 🌳 **Tree-sitter based code parsing** - Fast and accurate AST generation
- 🔧 **Dual interface** - Use as Python package or MCP server
- 🌍 **Multi-language support** - Python, JavaScript, TypeScript, Go pre-installed
- 📦 **Pre-built language packages** - No compilation needed
- 🚀 **Async/await support** - Non-blocking operations
- 🔌 **Extensible architecture** - Easy to add new tools and parsers
- ✨ **Actually works!** - Real parsing, not just failing tests
- 🤖 **MCP-compliant** - Works with Claude Desktop, Windsurf, Cursor, and other MCP clients

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourusername/mcp-code-parser.git
cd mcp-code-parser

# Basic install (includes Python, JS, TS, Go)
uv sync

# With development tools
uv sync --extra dev

# With C++ support
uv sync --extra cpp
```

### Using pip (Not Recommended)

```bash
# Install from source
git clone https://github.com/yourusername/mcp-code-parser.git
cd mcp-code-parser
pip install -e .

# You'll also need to manually install language packages:
pip install tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-go
```

**Note:** We recommend using `uv` for better dependency management and to ensure all packages work correctly.

## Quick Start

### Python Package Usage

```python
import asyncio
from mcp_code_parser import parse_code, parse_file

async def main():
    # Parse code directly
    result = await parse_code("def hello(): return 'world'", "python")
    if result.success:
        print(result.ast_text)
    
    # Parse from file (auto-detect language)
    result = await parse_file("example.py")
    print(f"Language: {result.language}")
    print(f"Nodes: {result.metadata['node_count']}")

asyncio.run(main())
```

### CLI Usage

**Always use `uv run` to ensure packages are available:**

```bash
# Parse a file
uv run mcp-code-parser parse example.py

# List supported languages
uv run mcp-code-parser languages

# Start the MCP server
uv run mcp-code-parser serve
```

**Alternative: Activate the virtual environment first:**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
mcp-code-parser parse example.py
mcp-code-parser serve
```

### MCP Server Usage

The mcp-code-parser MCP server is fully compliant with the Model Context Protocol and can be used with any MCP client including Claude Desktop, Windsurf, and Cursor.

#### Starting the MCP Server

**Important:** Always run with `uv run` to ensure the virtual environment is active:

```bash
# Start MCP server (stdio transport - default)
uv run mcp-code-parser serve

# Start with DEBUG logging
uv run mcp-code-parser serve --log-level DEBUG

# Start with custom log file
uv run mcp-code-parser serve --log-file /tmp/mcp-code-parser.log

# Start RESTful API server
uv run mcp-code-parser serve --rest --host 0.0.0.0 --port 8000
```

#### Installing in MCP Clients

All MCP clients use a similar configuration format. You'll need to add mcp-code-parser to the client's MCP servers configuration.

##### Common Configuration

Most MCP clients use this configuration structure:

```json
{
  "mcpServers": {
    "mcp-code-parser": {
      "command": "uv",
      "args": ["run", "mcp-code-parser", "serve"],
      "cwd": "/path/to/mcp-code-parser"
    }
  }
}
```

**Important**: Replace `/path/to/mcp-code-parser` with the actual path where you cloned this repository.

For debugging, add `--log-level DEBUG`:

```json
{
  "mcpServers": {
    "mcp-code-parser": {
      "command": "uv",
      "args": ["run", "mcp-code-parser", "serve", "--log-level", "DEBUG"],
      "cwd": "/path/to/mcp-code-parser"
    }
  }
}
```

##### Claude Desktop

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add the configuration above to this file. Create the file if it doesn't exist.

##### Cursor

**Config file location:**
- macOS: `~/.cursor/mcp/servers.json`
- Windows: `%USERPROFILE%\.cursor\mcp\servers.json`
- Linux: `~/.cursor/mcp/servers.json`

Add the configuration above to this file.

##### Windsurf

**Config file location:**
- macOS: `~/Library/Application Support/windsurf/mcp/servers.json`
- Windows: `%APPDATA%\windsurf\mcp\servers.json`
- Linux: `~/.config/windsurf/mcp/servers.json`

Add the configuration above to this file.

##### OpenAI Desktop

**Note**: As of writing, OpenAI Desktop MCP support is in development. Check the official documentation for the latest configuration method.

##### Verifying Installation

After adding the configuration:

1. Restart your MCP client
2. Look for "mcp-code-parser" in the available tools/extensions
3. Try using a tool like `parse_file` to verify it's working
4. Check logs in the `logs/` directory if you encounter issues

#### Available MCP Tools

The MCP server exposes the following tools:

- **parse_code** - Parse source code and return AST
  - Inputs: `content` (string), `language` (string)
  - Returns: AST representation with metadata

- **parse_file** - Parse code from a file  
  - Inputs: `file_path` (string), `language` (optional string)
  - Returns: AST representation with metadata

- **list_languages** - List supported programming languages
  - Returns: List of supported language identifiers

- **check_language** - Check if a language is supported
  - Inputs: `language` (string)
  - Returns: Support status and availability info

#### RESTful API

For direct HTTP integration, a RESTful API is available with the `--rest` flag. The API follows REST principles and JSON:API specification.

**Create an analysis:**
```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "source": {
      "content": "def hello(): return \"world\"",
      "language": "python"
    }
  }'
```

**Retrieve an analysis:**
```bash
curl http://localhost:8000/analyses/{id}
```

**List languages:**
```bash
curl http://localhost:8000/languages
```

**API Documentation:**
- OpenAPI specification: `/openapi.yaml`
- Full documentation: See [MCP vs REST comparison](docs/mcp-vs-rest.md)

## Documentation

📚 **[Read the comprehensive User Guide](docs/user-guide.md)** for detailed instructions on:
- Using the Python API with examples
- Setting up and using the RESTful API
- Integrating with MCP clients (Claude Desktop, Cursor, Windsurf)
- Understanding AST output
- Troubleshooting common issues

Additional documentation:
- [Technical Design](docs/tech-design.md) - Architecture and implementation details
- [MCP vs REST Comparison](docs/mcp-vs-rest.md) - Choosing between protocols
- [OpenAPI Specification](docs/openapi.yaml) - REST API reference

## Supported Languages

**Pre-installed:**
- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)
- Go (`.go`)

**Optional:**
- C++ (`.cpp`, `.cc`, `.hpp`, `.h`) - Install with `uv sync --extra cpp`

## API Reference

### Main Functions

#### `parse_code(content: str, language: str) -> ParseResult`
Parse source code content and return AST representation.

#### `parse_file(file_path: str, language: Optional[str] = None) -> ParseResult`
Parse source code from file. Auto-detects language if not specified.

#### `supported_languages() -> List[str]`
Get list of supported programming languages.

### ParseResult Object

```python
@dataclass
class ParseResult:
    language: str          # Detected/specified language
    ast_text: str         # Textual AST representation
    metadata: Dict        # Additional metadata
    error: Optional[str]  # Error message if failed
    success: bool         # Success indicator
```

## Architecture

The package is designed with extensibility in mind:

```
mcp_code_parser/
├── parsers/          # Parser implementations
│   ├── base.py       # Abstract base parser
│   └── tree_sitter.py
├── mcp_server.py     # MCP server implementation
├── api.py            # High-level Python API
└── cli.py            # Command-line interface
```

## Development

### Running Tests

```bash
# Using uv
uv run pytest
uv run pytest --cov=mcp_code_parser
uv run pytest tests/test_integration.py

# Or with activated virtual environment
pytest
pytest --cov=mcp_code_parser
pytest tests/test_integration.py

# Run only MCP protocol tests
uv run pytest tests/test_mcp_protocol.py

# Run only REST API tests
uv run pytest tests/test_rest_server.py

# Run only unit tests
uv run pytest tests/test_parser.py
```

The test suite includes:
- Unit tests for core functionality
- Integration tests for the Python API
- Integration tests for the MCP server (starts server automatically)
- Complex code parsing tests for all supported languages

### Adding a New Parser

1. Inherit from `BaseParser` in `mcp_code_parser.parsers.base`
2. Implement required methods
3. Register in parser configuration

### Adding Language Support

1. Add configuration to `mcp_code_parser.parsers.languages`
2. Specify grammar URL and node types
3. Test with complex code samples

## Troubleshooting

### "Language package not installed" error

If you get this error when running the server:
```json
{"error": "Language package tree-sitter-python not installed..."}
```

**Solution:** You're running the command outside the virtual environment. Use `uv run`:
```bash
# ❌ Wrong
mcp-code-parser serve

# ✅ Correct  
uv run mcp-code-parser serve
```

### Server not starting

Make sure no other process is using the port:
```bash
# Kill any existing mcp-code-parser servers
pkill -f "mcp-code-parser serve"

# Start fresh
uv run mcp-code-parser serve
```

### Can't find packages after installation

Make sure you're using the virtual environment:
```bash
# Check if packages are installed
uv pip list | grep tree-sitter

# Run commands with uv
uv run mcp-code-parser parse myfile.py
uv run mcp-code-parser serve
```

## License

Apache License 2.0 - see LICENSE file for details.
