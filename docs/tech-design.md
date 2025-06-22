# Technical Design Document

## Architecture Overview

The mcp-code-parser package provides a modular architecture for AI agent utilities with both direct Python API access and MCP (Model Control Protocol) endpoint exposure.

```
mcp-code-parser/
├── parsers/          # Code parsing implementations
│   ├── base.py       # Abstract base parser interface
│   ├── tree_sitter_parser.py  # Tree-sitter wrapper
│   └── languages/    # Language-specific optimizations
├── mcp/              # MCP server implementation
│   ├── server.py     # FastMCP server
│   └── tools.py      # MCP tool definitions
├── api.py            # High-level Python API
├── cache.py          # Caching utilities
└── utils.py          # Common utilities
```

## Core Components

### 1. Parser Interface (mcp_code_parser.parsers.base)

Abstract base class defining the parser contract:

```python
class BaseParser(ABC):
    @abstractmethod
    async def parse(self, content: str, language: str) -> ParseResult:
        """Parse code and return AST representation"""
        
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Return list of supported languages"""
```

### 2. Tree-Sitter Integration

**Dynamic Grammar Loading**:
- Grammars downloaded on first use
- Cached locally in `~/.cache/mcp-code-parser/grammars/`
- Version pinning for reproducibility

**AST Representation**:
- Textual format optimized for LLM consumption
- Hierarchical structure with indentation
- Filtered to exclude noise (whitespace, punctuation)

### 3. MCP Server

Built with FastMCP for easy tool exposure:

**Tools**:
- `parse_code`: Parse code file/content
- `list_languages`: Get supported languages
- `get_ast`: Get AST for code snippet

**Resources**:
- Grammar files
- Cached parse results

### 4. Caching Strategy

Two-level caching:
1. **Parse Cache**: LRU cache for parsed ASTs
2. **Grammar Cache**: Persistent cache for downloaded grammars

Cache keys include:
- Content hash
- Language
- Parser version

## Data Flow

1. **Direct API Usage**:
   ```
   User Code → API → Parser → Tree-Sitter → AST → Result
   ```

2. **MCP Usage**:
   ```
   MCP Client → FastMCP Server → Tool Handler → Parser → Result
   ```

## Language Support Implementation

Each language has:
1. Grammar URL and version
2. Optional AST filters
3. Optional custom formatting

Example configuration:
```python
LANGUAGE_CONFIG = {
    "python": {
        "grammar_url": "https://github.com/tree-sitter/tree-sitter-python",
        "version": "v0.20.4",
        "filters": ["exclude_comments", "simplify_strings"],
    }
}
```

## Error Handling

- **GrammarNotFoundError**: When grammar can't be downloaded
- **ParseError**: When code can't be parsed
- **LanguageNotSupportedError**: For unsupported languages
- Graceful degradation with partial results

## Performance Considerations

1. **Lazy Loading**: Grammars loaded only when needed
2. **Async Operations**: Non-blocking I/O for downloads
3. **Efficient Caching**: Minimize repeated parsing
4. **Memory Management**: Configurable cache sizes

## Security

1. **Grammar Verification**: Checksum validation
2. **Sandboxed Parsing**: No code execution
3. **Resource Limits**: Max file size, parse timeout
4. **MCP Authentication**: Optional token-based auth

## Extensibility

New tools can be added by:
1. Implementing BaseParser interface
2. Registering in tool factory
3. Adding MCP tool definition

Example:
```python
@register_parser("ast_differ")
class ASTDiffer(BaseParser):
    # Implementation
```

## Testing Strategy

1. **Unit Tests**: Each component isolated
2. **Integration Tests**: Complex real-world code
3. **Performance Tests**: Large file handling
4. **MCP Tests**: Server endpoint validation