"""Integration tests for MCP server."""

import asyncio
import json
import multiprocessing
import time
from typing import Optional

import httpx
import pytest
import uvicorn

from agent_tools.mcp.server import mcp


def _run_mcp_server(host: str, port: int):
    """Run the MCP server - needs to be at module level for pickling."""
    # Use the http_app from FastMCP
    uvicorn.run(mcp.http_app(), host=host, port=port, log_level="error")


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
                # Try to call the health_check tool
                response = httpx.post(
                    f"http://{self.host}:{self.port}/tools/health_check",
                    json={}
                )
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
async def test_mcp_parse_code(mcp_client):
    """Test parse_code tool via MCP."""
    response = await mcp_client.post(
        "/tools/parse_code",
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
    assert "hello" in data["ast"]
    assert data["error"] is None


@pytest.mark.asyncio
async def test_mcp_parse_file(mcp_client, tmp_path):
    """Test parse_file tool via MCP."""
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
        "/tools/parse_file",
        json={
            "file_path": str(test_file)
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["language"] == "javascript"
    assert "program" in data["ast"]
    assert "function_declaration" in data["ast"]
    assert "add" in data["ast"]


@pytest.mark.asyncio
async def test_mcp_list_languages(mcp_client):
    """Test list_supported_languages tool via MCP."""
    response = await mcp_client.post("/tools/list_supported_languages", json={})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "languages" in data
    assert isinstance(data["languages"], list)
    assert len(data["languages"]) >= 5
    assert "python" in data["languages"]
    assert "javascript" in data["languages"]
    assert data["count"] == len(data["languages"])


@pytest.mark.asyncio
async def test_mcp_check_language_available(mcp_client):
    """Test check_language_available tool via MCP."""
    # Test supported language
    response = await mcp_client.post(
        "/tools/check_language_available",
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
        "/tools/check_language_available",
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
    """Test parse_code error handling via MCP."""
    response = await mcp_client.post(
        "/tools/parse_code",
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
    """Test parse_file with non-existent file via MCP."""
    response = await mcp_client.post(
        "/tools/parse_file",
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
async def test_mcp_resource_parsers_info(mcp_client):
    """Test parsers/info resource via MCP."""
    response = await mcp_client.get("/resources/agent-tools://parsers/info")
    
    assert response.status_code == 200
    info = response.text
    
    assert "Available parsers" in info
    assert "tree-sitter" in info
    assert "Supported languages" in info
    assert "python" in info


@pytest.mark.asyncio
async def test_mcp_concurrent_requests(mcp_client):
    """Test handling concurrent requests via MCP."""
    # Create multiple parse tasks
    tasks = []
    for i in range(5):
        task = mcp_client.post(
            "/tools/parse_code",
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
        assert f"test{i}" in data["ast"]


@pytest.mark.asyncio
async def test_mcp_parse_complex_code(mcp_client):
    """Test parsing complex code via MCP."""
    complex_code = """
from typing import List, Optional
import asyncio

class DataProcessor:
    def __init__(self, workers: int = 4):
        self.workers = workers
        self.queue: asyncio.Queue = asyncio.Queue()
    
    async def process(self, items: List[str]) -> List[dict]:
        tasks = []
        for item in items:
            task = asyncio.create_task(self._process_item(item))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _process_item(self, item: str) -> dict:
        await asyncio.sleep(0.1)
        return {"item": item, "processed": True}

@dataclass
class Config:
    timeout: int = 30
    retries: int = 3
"""
    
    response = await mcp_client.post(
        "/tools/parse_code",
        json={
            "content": complex_code,
            "language": "python"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "class_definition" in data["ast"]
    assert "DataProcessor" in data["ast"]
    assert "function_definition" in data["ast"]
    assert "decorator" in data["ast"] or "decorated_definition" in data["ast"]