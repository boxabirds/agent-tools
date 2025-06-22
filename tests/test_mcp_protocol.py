"""Integration tests for MCP protocol server."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest


class MCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self, server_process):
        self.process = server_process
        self.request_id = 0
        
    def send_request(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC request and get response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id,
            "params": params or {}
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
    
    def send_notification(self, method: str, params: dict = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        self.process.stdin.write(json.dumps(notification) + "\n")
        self.process.stdin.flush()


@pytest.fixture
def mcp_client():
    """Create an MCP client connected to the server."""
    # Start the MCP server using uv run to ensure virtual env is active
    server_process = subprocess.Popen(
        ["uv", "run", "mcp-code-parser", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).parent.parent  # Run from project root
    )
    
    client = MCPClient(server_process)
    
    # Initialize the connection
    init_response = client.send_request(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    )
    
    assert "result" in init_response
    assert init_response["result"]["protocolVersion"] == "2024-11-05"
    
    # Send initialized notification
    client.send_notification("notifications/initialized")
    
    yield client
    
    # Cleanup
    server_process.terminate()
    server_process.wait(timeout=5)


def test_server_info(mcp_client):
    """Test that server returns correct info during initialization."""
    # We already tested this in the fixture, but let's be explicit
    # The server info was returned in the initialize response
    # which we validated in the fixture
    pass


def test_list_tools(mcp_client):
    """Test listing available tools."""
    response = mcp_client.send_request("tools/list")
    
    assert "result" in response
    tools = response["result"]["tools"]
    
    # Check we have the expected tools
    tool_names = [tool["name"] for tool in tools]
    assert "parse_code" in tool_names
    assert "parse_file" in tool_names
    assert "list_languages" in tool_names
    assert "check_language" in tool_names
    
    # Check parse_code tool details
    parse_code_tool = next(t for t in tools if t["name"] == "parse_code")
    assert "description" in parse_code_tool
    assert "inputSchema" in parse_code_tool
    assert parse_code_tool["inputSchema"]["required"] == ["content", "language"]


def test_call_parse_code(mcp_client):
    """Test calling the parse_code tool."""
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "parse_code",
            "arguments": {
                "content": "def hello():\n    return 'world'",
                "language": "python"
            }
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    assert len(content) > 0
    assert content[0]["type"] == "text"
    
    # Parse the JSON result
    result = json.loads(content[0]["text"])
    assert result["success"] is True
    assert result["language"] == "python"
    assert "module" in result["ast"]
    assert "function_definition" in result["ast"]


def test_call_list_languages(mcp_client):
    """Test calling the list_languages tool."""
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "list_languages",
            "arguments": {}
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert "languages" in result
    assert "python" in result["languages"]
    assert "javascript" in result["languages"]
    assert "typescript" in result["languages"]
    assert "go" in result["languages"]


def test_call_check_language(mcp_client):
    """Test calling the check_language tool."""
    # Check supported language
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "check_language",
            "arguments": {"language": "python"}
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert result["language"] == "python"
    assert result["supported"] is True
    assert result["grammar_available"] is True
    
    # Check unsupported language
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "check_language",
            "arguments": {"language": "cobol"}
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert result["language"] == "cobol"
    assert result["supported"] is False
    assert result["grammar_available"] is False


def test_parse_complex_code(mcp_client):
    """Test parsing more complex code."""
    complex_code = '''
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        return x + y
    
    def multiply(self, x, y):
        return x * y
'''
    
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "parse_code",
            "arguments": {
                "content": complex_code,
                "language": "python"
            }
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert result["success"] is True
    assert "class_definition" in result["ast"]
    assert result["metadata"]["node_count"] > 20  # Complex code has many nodes


def test_parse_javascript(mcp_client):
    """Test parsing JavaScript code."""
    js_code = '''
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

const result = fibonacci(10);
console.log(result);
'''
    
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "parse_code",
            "arguments": {
                "content": js_code,
                "language": "javascript"
            }
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert result["success"] is True
    assert result["language"] == "javascript"
    assert "function_declaration" in result["ast"]


def test_error_handling(mcp_client):
    """Test error handling for invalid inputs."""
    # Invalid language
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "parse_code",
            "arguments": {
                "content": "print('hello')",
                "language": "invalid-language"
            }
        }
    )
    
    assert "result" in response
    content = response["result"]["content"]
    result = json.loads(content[0]["text"])
    
    assert result["success"] is False
    assert result["error"] is not None
    
    # Missing required argument
    response = mcp_client.send_request(
        "tools/call",
        {
            "name": "parse_code",
            "arguments": {
                "content": "print('hello')"
                # Missing language
            }
        }
    )
    
    # FastMCP returns validation errors as successful responses with isError=True
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "validation error" in response["result"]["content"][0]["text"]