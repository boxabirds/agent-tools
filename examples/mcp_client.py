"""Example MCP client for agent-tools."""

import asyncio
import httpx
import json


async def call_mcp_tool(tool_name: str, params: dict):
    """Call an MCP tool via HTTP."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/tools/{tool_name}",
            json=params
        )
        return response.json()


async def example_mcp_usage():
    """Example of using agent-tools via MCP."""
    print("=== MCP Client Example ===")
    print("Note: Make sure the MCP server is running (agent-tools serve)")
    
    # Example 1: Parse code via MCP
    print("\n1. Parsing Python code:")
    result = await call_mcp_tool("parse_code", {
        "content": "def greet(name):\n    return f'Hello, {name}!'",
        "language": "python"
    })
    print(json.dumps(result, indent=2))
    
    # Example 2: List supported languages
    print("\n2. Listing supported languages:")
    result = await call_mcp_tool("list_supported_languages", {})
    print(json.dumps(result, indent=2))
    
    # Example 3: Check if language is available
    print("\n3. Checking language availability:")
    result = await call_mcp_tool("check_language_available", {
        "language": "python"
    })
    print(json.dumps(result, indent=2))


async def example_mcp_file_parsing():
    """Example of parsing files via MCP."""
    print("\n=== MCP File Parsing Example ===")
    
    # Create a test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
        f.write("""
interface User {
    id: string;
    name: string;
}

class UserManager {
    private users: Map<string, User> = new Map();
    
    addUser(user: User): void {
        this.users.set(user.id, user);
    }
    
    getUser(id: string): User | undefined {
        return this.users.get(id);
    }
}
""")
        temp_path = f.name
    
    # Parse via MCP
    result = await call_mcp_tool("parse_file", {
        "file_path": temp_path
    })
    
    print(f"Parsed TypeScript file: {temp_path}")
    print(f"Success: {result.get('success')}")
    print(f"Language: {result.get('language')}")
    print(f"AST preview (first 300 chars):")
    print(result.get('ast', '')[:300])
    
    # Clean up
    import os
    os.unlink(temp_path)


async def main():
    """Run MCP examples."""
    try:
        await example_mcp_usage()
        await example_mcp_file_parsing()
    except httpx.ConnectError:
        print("Error: Could not connect to MCP server.")
        print("Please start the server with: agent-tools serve")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())