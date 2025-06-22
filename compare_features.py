#!/usr/bin/env python3
"""Compare what tree-sitter provides vs what agent-tools adds."""

print("=== TREE-SITTER NATIVE CAPABILITIES ===\n")

print("1. Core Parsing:")
print("   - Parser class to parse code into AST")
print("   - Node class representing AST nodes")
print("   - Tree class representing the parse tree")
print("   - Language class for language grammars")
print("   - Query class for pattern matching in AST")
print("")

print("2. What you need to do manually:")
print("   - Install each language grammar separately")
print("   - Load language modules and create Language objects")
print("   - Handle file I/O and encoding issues")
print("   - Format AST output (nodes have no built-in pretty printing)")
print("   - Detect language from file extensions")
print("   - Error handling and recovery")
print("   - No async support out of the box")
print("")

print("3. Example native tree-sitter usage:")
print("""
import tree_sitter
import tree_sitter_python

# Manual setup required
PY_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
parser = tree_sitter.Parser(PY_LANGUAGE)

# Parse code
tree = parser.parse(b"def hello(): pass")
root = tree.root_node

# Manual traversal needed
def print_tree(node, indent=0):
    print("  " * indent + node.type)
    for child in node.children:
        print_tree(child, indent + 1)
""")

print("\n=== AGENT-TOOLS ADDITIONS ===\n")

print("1. High-Level API:")
print("   - Simple parse_code() and parse_file() functions")
print("   - Automatic language detection from file extensions")
print("   - Built-in async/await support")
print("   - Consistent ParseResult object with metadata")
print("")

print("2. Language Management:")
print("   - Pre-configured language settings for Python, JS, TS, Go, C++")
print("   - Automatic grammar loading (no manual Language object creation)")
print("   - Filtered AST output showing only relevant node types")
print("   - File extension to language mapping")
print("")

print("3. AST Formatting:")
print("   - Human-readable AST text representation")
print("   - Configurable node filtering (include/exclude specific types)")
print("   - Leaf node text included in output")
print("   - Proper indentation and structure")
print("")

print("4. Error Handling:")
print("   - Graceful handling of missing language packages")
print("   - Safe file reading with encoding detection")
print("   - Structured error reporting in ParseResult")
print("")

print("5. MCP Server Integration:")
print("   - Exposes parsing as MCP tools for AI agents")
print("   - Works with Claude Desktop, Cursor, Windsurf")
print("   - Logging and debugging support")
print("   - Both stdio and HTTP transports")
print("")

print("6. CLI Interface:")
print("   - Command-line tool for parsing files")
print("   - List supported languages")
print("   - Start MCP server easily")
print("")

print("7. Extensibility:")
print("   - Abstract BaseParser for adding new parsers")
print("   - Plugin architecture for future tools")
print("   - Consistent API across different parsers")
print("")

print("=== VALUE ASSESSMENT ===\n")

print("MEANINGFUL ADDITIONS:")
print("✓ MCP server integration - Genuinely useful for AI agent workflows")
print("✓ Filtered AST output - Shows only relevant nodes, not entire tree")
print("✓ Language configurations - Pre-tuned node filtering for each language")
print("✓ Async API - Important for non-blocking operations")
print("✓ Unified error handling - Consistent ParseResult structure")
print("✓ File encoding detection - Handles real-world files better")
print("")

print("THIN WRAPPERS:")
print("- Basic parsing is just calling tree-sitter.Parser.parse()")
print("- Language detection is simple file extension mapping")
print("- AST formatting is basic tree traversal")
print("")

print("CONCLUSION:")
print("Agent-tools adds real value for AI agent use cases by:")
print("1. Making tree-sitter accessible via MCP protocol")
print("2. Providing filtered, relevant AST output (not raw parse trees)")
print("3. Handling the boilerplate of language setup and error handling")
print("4. Creating a consistent async API for integration")
print("")
print("It's more than a trivial wrapper - it's a purposeful adaptation")
print("of tree-sitter for AI agent workflows, especially the MCP integration.")