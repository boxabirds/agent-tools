# agent-tools

AI agent tools providing both Python package interface and MCP endpoint for various utilities. The initial implementation focuses on tree-sitter based code parsing with support for multiple programming languages.

## Features

- 🌳 **Tree-sitter based code parsing** - Fast and accurate AST generation
- 🔧 **Dual interface** - Use as Python package or MCP server
- 🌍 **Multi-language support** - Python, JavaScript, TypeScript, Go, C++
- 📦 **Dynamic grammar loading** - Downloads language grammars on-demand
- 🚀 **Async/await support** - Non-blocking operations
- 🔌 **Extensible architecture** - Easy to add new tools and parsers

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/agent-tools.git
cd agent-tools
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

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

```bash
# Parse a file
agent-tools parse example.py

# List supported languages
agent-tools languages

# Start MCP server
agent-tools serve
```

### MCP Server Usage

Start the server:
```bash
agent-tools serve
```

Then use the MCP tools:
- `parse_code` - Parse source code content
- `parse_file` - Parse source code from file
- `list_supported_languages` - Get supported languages
- `check_language_available` - Check if language grammar is available

## Supported Languages

- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)
- Go (`.go`)
- C++ (`.cpp`, `.cc`, `.hpp`, `.h`)

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
│   └── server.py     # FastMCP implementation
├── api.py            # High-level Python API
└── cli.py            # Command-line interface
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent_tools

# Run specific test file
pytest tests/test_integration.py

# Run only MCP server tests
pytest tests/test_mcp_server.py

# Run only unit tests
pytest tests/test_parser.py
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

## License

Apache License 2.0 - see LICENSE file for details.
