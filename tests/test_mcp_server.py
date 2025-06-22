"""Integration tests for simple HTTP server."""

import asyncio
import json
import multiprocessing
import time
from typing import Optional

import httpx
import pytest

from mcp_code_parser.mcp_http_server import run_server


def _run_mcp_server(host: str, port: int):
    """Run the MCP server - needs to be at module level for pickling."""
    run_server(host, port)


class MCPServerProcess:
    """Manager for MCP server subprocess."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.process: Optional[multiprocessing.Process] = None
        
    def start(self):
        """Start the MCP server in a subprocess."""
        self.process = multiprocessing.Process(
            target=_run_mcp_server, 
            args=(self.host, self.port)
        )
        self.process.start()
        
        # Wait for server to be ready
        self._wait_for_server()
    
    def stop(self):
        """Stop the MCP server."""
        if self.process:
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
    
    def _wait_for_server(self, timeout: int = 10):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try health check endpoint
                response = httpx.get(f"http://{self.host}:{self.port}/health")
                if response.status_code == 200:
                    return
            except httpx.ConnectError:
                pass
            time.sleep(0.1)
        raise TimeoutError("MCP server did not start in time")


@pytest.fixture(scope="module")
def mcp_server():
    """Start MCP server for tests."""
    server = MCPServerProcess()
    server.start()
    yield server
    server.stop()


@pytest.fixture
async def mcp_client(mcp_server):
    """Create HTTP client for MCP server."""
    async with httpx.AsyncClient(base_url=f"http://{mcp_server.host}:{mcp_server.port}") as client:
        yield client


@pytest.mark.asyncio
async def test_mcp_health_check(mcp_client):
    """Test health check endpoint."""
    response = await mcp_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "agent-tools"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_mcp_list_languages(mcp_client):
    """Test list languages endpoint."""
    response = await mcp_client.get("/languages")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "languages" in data
    assert isinstance(data["languages"], list)
    assert len(data["languages"]) >= 5
    assert "python" in data["languages"]
    assert "javascript" in data["languages"]
    assert data["count"] == len(data["languages"])


@pytest.mark.asyncio
async def test_mcp_info(mcp_client):
    """Test info endpoint."""
    response = await mcp_client.get("/info")
    
    assert response.status_code == 200
    info = response.text
    
    assert "Available parsers" in info
    assert "tree-sitter" in info
    assert "Supported languages" in info
    assert "python" in info


@pytest.mark.asyncio
async def test_mcp_parse_code(mcp_client):
    """Test parse code endpoint."""
    response = await mcp_client.post(
        "/parse",
        json={
            "content": "def hello(name):\n    return f'Hello, {name}!'",
            "language": "python"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["language"] == "python"
    assert "module" in data["ast"]
    assert "function_definition" in data["ast"]
    assert data["error"] is None


@pytest.mark.asyncio
async def test_mcp_parse_file(mcp_client, tmp_path):
    """Test parse file endpoint."""
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
function add(a, b) {
    return a + b;
}

const result = add(1, 2);
console.log(result);
""")
    
    response = await mcp_client.post(
        "/parse-file",
        json={
            "file_path": str(test_file)
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["language"] == "javascript"
    assert "program" in data["ast"]
    assert "function" in data["ast"]
    assert data["error"] is None


@pytest.mark.asyncio
async def test_mcp_check_language_available(mcp_client):
    """Test check language endpoint."""
    # Test supported language
    response = await mcp_client.post(
        "/check-language",
        json={"language": "python"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["language"] == "python"
    assert data["supported"] is True
    assert isinstance(data["grammar_available"], bool)
    assert "message" in data
    
    # Test unsupported language
    response = await mcp_client.post(
        "/check-language",
        json={"language": "unsupported_lang"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["language"] == "unsupported_lang"
    assert data["supported"] is False
    assert data["grammar_available"] is False
    assert "not supported" in data["message"]


@pytest.mark.asyncio
async def test_mcp_parse_code_error(mcp_client):
    """Test parse code error handling."""
    response = await mcp_client.post(
        "/parse",
        json={
            "content": "print('hello')",
            "language": "invalid_language"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["error"] is not None
    assert "not supported" in data["error"]


@pytest.mark.asyncio
async def test_mcp_parse_file_not_found(mcp_client):
    """Test parse file with non-existent file."""
    response = await mcp_client.post(
        "/parse-file",
        json={
            "file_path": "/path/to/nonexistent/file.py"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["error"] is not None
    assert "Error reading file" in data["error"]


@pytest.mark.asyncio
async def test_mcp_missing_required_fields(mcp_client):
    """Test endpoints with missing required fields."""
    # Parse without content
    response = await mcp_client.post(
        "/parse",
        json={"language": "python"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Missing required fields" in data["error"]
    
    # Parse file without file_path
    response = await mcp_client.post(
        "/parse-file",
        json={}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Missing required field" in data["error"]
    
    # Check language without language
    response = await mcp_client.post(
        "/check-language",
        json={}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Missing required field" in data["error"]


@pytest.mark.asyncio
async def test_mcp_invalid_json(mcp_client):
    """Test invalid JSON handling."""
    response = await mcp_client.post(
        "/parse",
        content=b"invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid JSON" in data["error"]


@pytest.mark.asyncio
async def test_mcp_404_endpoints(mcp_client):
    """Test 404 handling."""
    response = await mcp_client.get("/nonexistent")
    assert response.status_code == 404
    
    response = await mcp_client.post("/nonexistent", json={})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mcp_concurrent_requests(mcp_client):
    """Test handling concurrent requests."""
    # Create multiple parse tasks
    tasks = []
    for i in range(5):
        task = mcp_client.post(
            "/parse",
            json={
                "content": f"function test{i}() {{ return {i}; }}",
                "language": "javascript"
            }
        )
        tasks.append(task)
    
    # Execute concurrently
    responses = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    for i, response in enumerate(responses):
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "javascript"