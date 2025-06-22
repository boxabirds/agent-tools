# agent-tools

AI agent tools providing both Python package interface and MCP endpoint for various utilities. The initial implementation focuses on tree-sitter based code parsing with support for multiple programming languages.

## Features

- 🌳 **Tree-sitter based code parsing** - Fast and accurate AST generation
- 🔧 **Dual interface** - Use as Python package or MCP server
- 🌍 **Multi-language support** - Python, JavaScript, TypeScript, Go pre-installed
- 📦 **Pre-built language packages** - No compilation needed
- 🚀 **Async/await support** - Non-blocking operations
- 🔌 **Extensible architecture** - Easy to add new tools and parsers
- ✨ **Actually works!** - Real parsing, not just failing tests

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourusername/agent-tools.git
cd agent-tools

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
git clone https://github.com/yourusername/agent-tools.git
cd agent-tools
pip install -e .

# You'll also need to manually install language packages:
pip install tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-go
```

**Note:** We recommend using `uv` for better dependency management and to ensure all packages work correctly.

## Quick Start

### Python Package Usage

```python
import asyncio
from agent_tools import parse_code, parse_file

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
uv run agent-tools parse example.py

# List supported languages
uv run agent-tools languages

# Start the MCP server
uv run agent-tools serve
```

**Alternative: Activate the virtual environment first:**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
agent-tools parse example.py
agent-tools serve
```

### MCP Server Usage

**Important:** Always run with `uv run` to ensure the virtual environment is active:

```bash
# Start the server (CORRECT way)
uv run agent-tools serve

# With custom host/port
uv run agent-tools serve --host 0.0.0.0 --port 3000

# ⚠️ This WON'T work - packages won't be found
# agent-tools serve  # DON'T do this
```

The server provides a simple HTTP API:

**GET Endpoints:**
- `/health` - Health check
- `/languages` - List supported languages
- `/info` - Parser information

**POST Endpoints:**
- `/parse` - Parse source code
  ```json
  {"content": "def hello(): pass", "language": "python"}
  ```
- `/parse-file` - Parse from file
  ```json
  {"file_path": "/path/to/file.py", "language": "python"}
  ```
- `/check-language` - Check language support
  ```json
  {"language": "python"}
  ```

**Example:**
```bash
# Parse code
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"content": "def hello(): pass", "language": "python"}'

# Check health
curl http://localhost:8000/health
```

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
agent_tools/
├── parsers/          # Parser implementations
│   ├── base.py       # Abstract base parser
│   └── tree_sitter_parser.py
├── mcp/              # MCP server
│   └── server.py     # Simple HTTP server
├── api.py            # High-level Python API
└── cli.py            # Command-line interface
```

## Development

### Running Tests

```bash
# Using uv
uv run pytest
uv run pytest --cov=agent_tools
uv run pytest tests/test_integration.py

# Or with activated virtual environment
pytest
pytest --cov=agent_tools
pytest tests/test_integration.py

# Run only MCP server tests
uv run pytest tests/test_mcp_server.py

# Run only unit tests
uv run pytest tests/test_parser.py
```

The test suite includes:
- Unit tests for core functionality
- Integration tests for the Python API
- Integration tests for the MCP server (starts server automatically)
- Complex code parsing tests for all supported languages

### Adding a New Parser

1. Inherit from `BaseParser` in `agent_tools.parsers.base`
2. Implement required methods
3. Register in `AgentTools` class

### Adding Language Support

1. Add configuration to `agent_tools.parsers.languages`
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
agent-tools serve

# ✅ Correct  
uv run agent-tools serve
```

### Server not starting

Make sure no other process is using the port:
```bash
# Kill any existing agent-tools servers
pkill -f "agent-tools serve"

# Start fresh
uv run agent-tools serve
```

### Can't find packages after installation

Make sure you're using the virtual environment:
```bash
# Check if packages are installed
uv pip list | grep tree-sitter

# Run commands with uv
uv run agent-tools parse myfile.py
uv run agent-tools serve
```

## License

Apache License 2.0 - see LICENSE file for details.
