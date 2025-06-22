"""Basic usage examples for mcp-code-parser."""

import asyncio
from mcp_code_parser import parse_code, parse_file, supported_languages


async def example_parse_code():
    """Example: Parse code directly."""
    print("=== Parse Code Example ===")
    
    python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""
    
    result = await parse_code(python_code, "python")
    
    if result.success:
        print(f"Language: {result.language}")
        print(f"AST Preview (first 500 chars):")
        print(result.ast_text[:500])
        print(f"...\nTotal nodes: {result.metadata['node_count']}")
    else:
        print(f"Error: {result.error}")


async def example_parse_file():
    """Example: Parse file with auto-detection."""
    print("\n=== Parse File Example ===")
    
    # Create a temporary file for demonstration
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write("""
// JavaScript example
const users = [
    { name: 'Alice', age: 30 },
    { name: 'Bob', age: 25 }
];

function findUserByName(name) {
    return users.find(user => user.name === name);
}

class UserService {
    constructor() {
        this.users = new Map();
    }
    
    addUser(user) {
        this.users.set(user.name, user);
    }
}
""")
        temp_path = f.name
    
    # Parse the file (language auto-detected from .js extension)
    result = await parse_file(temp_path)
    
    if result.success:
        print(f"Auto-detected language: {result.language}")
        print(f"File: {temp_path}")
        print(f"AST Preview (first 500 chars):")
        print(result.ast_text[:500])
    
    # Clean up
    import os
    os.unlink(temp_path)


async def example_list_languages():
    """Example: List supported languages."""
    print("\n=== Supported Languages ===")
    
    languages = supported_languages()
    print(f"Total supported languages: {len(languages)}")
    for lang in sorted(languages):
        print(f"  - {lang}")


async def example_with_api_class():
    """Example: Using the AgentTools class directly."""
    print("\n=== AgentTools Class Example ===")
    
    from mcp_code_parser import AgentTools
    
    tools = AgentTools()
    
    # List available parsers
    parsers = tools.list_parsers()
    print(f"Available parsers: {', '.join(parsers)}")
    
    # Parse Go code
    go_code = """
package main

import "fmt"

func main() {
    message := "Hello, World!"
    fmt.Println(message)
}
"""
    
    result = await tools.parse_code(go_code, "go")
    if result.success:
        print(f"\nParsed Go code successfully")
        print(f"AST contains: {result.ast_text.count('function_declaration')} function declarations")


async def example_error_handling():
    """Example: Error handling."""
    print("\n=== Error Handling Example ===")
    
    # Try to parse with unsupported language
    result = await parse_code("print('hello')", "unsupported_language")
    if not result.success:
        print(f"Expected error: {result.error}")
    
    # Try to parse invalid file
    result = await parse_file("/path/that/does/not/exist.py")
    if not result.success:
        print(f"File error: {result.error}")


async def main():
    """Run all examples."""
    await example_parse_code()
    await example_parse_file()
    await example_list_languages()
    await example_with_api_class()
    await example_error_handling()


if __name__ == "__main__":
    asyncio.run(main())