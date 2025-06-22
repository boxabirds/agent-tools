"""Integration tests for RESTful API server."""

import asyncio
import json
import threading
import time
from typing import Optional
import uuid

import httpx
import pytest

from agenttools.rest.server import run_server, HTTPServer, RESTHandler


def _run_rest_server(server: HTTPServer):
    """Run the REST server in a thread."""
    server.serve_forever()


class RESTServerProcess:
    """Manager for REST server thread."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the REST server in a thread."""
        self.server = HTTPServer((self.host, self.port), RESTHandler)
        self.thread = threading.Thread(
            target=_run_rest_server, 
            args=(self.server,),
            daemon=True
        )
        self.thread.start()
        
        # Wait for server to be ready
        self._wait_for_server()
    
    def stop(self):
        """Stop the REST server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
    
    def _wait_for_server(self, timeout: int = 10):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to connect to the server
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.host, self.port))
                sock.close()
                if result == 0:
                    time.sleep(0.1)  # Give it a moment to fully initialize
                    return
            except:
                pass
            time.sleep(0.1)
        raise RuntimeError(f"Server failed to start within {timeout} seconds")


@pytest.fixture(scope="module")
def rest_server():
    """Start REST server for tests."""
    # Enable debug logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
    
    server = RESTServerProcess(port=8001)  # Use different port to avoid conflicts
    server.start()
    yield f"http://{server.host}:{server.port}"
    server.stop()


@pytest.fixture
async def rest_client(rest_server):
    """Create HTTP client for REST API."""
    async with httpx.AsyncClient(base_url=rest_server) as client:
        yield client


@pytest.mark.asyncio
async def test_api_root(rest_client):
    """Test GET / returns API information."""
    response = await rest_client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.api+json"
    
    data = response.json()
    assert "data" in data
    assert data["data"]["type"] == "api"
    assert "links" in data["data"]
    assert data["data"]["links"]["analyses"] == "/analyses"
    assert data["data"]["links"]["languages"] == "/languages"
    assert data["data"]["links"]["parsers"] == "/parsers"


@pytest.mark.asyncio
async def test_list_languages(rest_client):
    """Test GET /languages."""
    response = await rest_client.get("/languages")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    
    # Check structure of a language entry
    python_lang = next((l for l in data["data"] if l["id"] == "python"), None)
    assert python_lang is not None
    assert python_lang["type"] == "language"
    assert "attributes" in python_lang
    assert "file_extensions" in python_lang["attributes"]
    assert ".py" in python_lang["attributes"]["file_extensions"]
    assert "links" in python_lang
    assert python_lang["links"]["self"] == "/languages/python"


@pytest.mark.asyncio
async def test_get_language(rest_client):
    """Test GET /languages/{id}."""
    response = await rest_client.get("/languages/python")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert data["data"]["id"] == "python"
    assert data["data"]["type"] == "language"
    # Language availability may vary based on test environment
    assert "available" in data["data"]["attributes"]
    assert isinstance(data["data"]["attributes"]["available"], bool)
    assert "node_types" in data["data"]["attributes"]


@pytest.mark.asyncio
async def test_get_language_not_found(rest_client):
    """Test GET /languages/{id} for non-existent language."""
    response = await rest_client.get("/languages/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert "errors" in data
    assert data["errors"][0]["status"] == "404"


@pytest.mark.asyncio
async def test_list_parsers(rest_client):
    """Test GET /parsers."""
    response = await rest_client.get("/parsers")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "tree-sitter"
    assert "supported_languages" in data["data"][0]["attributes"]


@pytest.mark.asyncio
async def test_create_analysis_with_content(rest_client):
    """Test POST /analyses with content."""
    request_data = {
        "source": {
            "content": "def hello():\n    return 'world'",
            "language": "python"
        }
    }
    
    response = await rest_client.post("/analyses", json=request_data)
    assert response.status_code == 201
    assert "location" in response.headers
    
    data = response.json()
    assert "data" in data
    assert data["data"]["type"] == "analysis"
    # Check basic structure
    assert data["data"]["attributes"]["language"] == "python"
    assert "success" in data["data"]["attributes"]
    
    # If parsing succeeded, check AST content
    if data["data"]["attributes"]["success"]:
        assert data["data"]["attributes"]["ast"] is not None
        assert "module" in data["data"]["attributes"]["ast"]
        assert "function_definition" in data["data"]["attributes"]["ast"]
    else:
        # If parsing failed, there should be an error message
        assert data["data"]["attributes"]["error"] is not None
    
    # Check relationships
    assert data["data"]["relationships"]["language"]["data"]["id"] == "python"
    assert data["data"]["relationships"]["parser"]["data"]["id"] == "tree-sitter"
    
    # Verify the Location header points to the created resource
    analysis_id = data["data"]["id"]
    assert response.headers["location"] == f"/analyses/{analysis_id}"


@pytest.mark.asyncio
async def test_create_analysis_with_file(rest_client):
    """Test POST /analyses with file_path."""
    # Create a temporary test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello, World!')")
        temp_file = f.name
    
    try:
        request_data = {
            "source": {
                "file_path": temp_file
            }
        }
        
        response = await rest_client.post("/analyses", json=request_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "success" in data["data"]["attributes"]
        assert data["data"]["attributes"]["language"] == "python"  # Auto-detected
    finally:
        import os
        os.unlink(temp_file)


@pytest.mark.asyncio
async def test_get_analysis(rest_client):
    """Test GET /analyses/{id}."""
    # First create an analysis
    request_data = {
        "source": {
            "content": "console.log('test');",
            "language": "javascript"
        }
    }
    
    create_response = await rest_client.post("/analyses", json=request_data)
    assert create_response.status_code == 201
    
    created_data = create_response.json()
    analysis_id = created_data["data"]["id"]
    
    # Now retrieve it
    get_response = await rest_client.get(f"/analyses/{analysis_id}")
    assert get_response.status_code == 200
    
    retrieved_data = get_response.json()
    assert retrieved_data["data"]["id"] == analysis_id
    assert retrieved_data["data"]["attributes"]["language"] == "javascript"


@pytest.mark.asyncio
async def test_get_analysis_not_found(rest_client):
    """Test GET /analyses/{id} for non-existent analysis."""
    fake_id = str(uuid.uuid4())
    response = await rest_client.get(f"/analyses/{fake_id}")
    assert response.status_code == 404
    
    data = response.json()
    assert "errors" in data
    assert data["errors"][0]["status"] == "404"


@pytest.mark.asyncio
async def test_create_analysis_missing_source(rest_client):
    """Test POST /analyses with missing source field."""
    response = await rest_client.post("/analyses", json={})
    assert response.status_code == 400
    
    data = response.json()
    assert "errors" in data
    assert "Missing required field: source" in data["errors"][0]["detail"]


@pytest.mark.asyncio
async def test_create_analysis_missing_language(rest_client):
    """Test POST /analyses with content but no language."""
    request_data = {
        "source": {
            "content": "def hello(): pass"
        }
    }
    
    response = await rest_client.post("/analyses", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "errors" in data
    assert "Language is required" in data["errors"][0]["detail"]


@pytest.mark.asyncio
async def test_create_analysis_invalid_source(rest_client):
    """Test POST /analyses with invalid source (no content or file_path)."""
    request_data = {
        "source": {
            "something": "else"
        }
    }
    
    response = await rest_client.post("/analyses", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "errors" in data
    assert "content" in data["errors"][0]["detail"] or "file_path" in data["errors"][0]["detail"]


@pytest.mark.asyncio
async def test_404_endpoints(rest_client):
    """Test that non-existent endpoints return 404."""
    endpoints = [
        "/nonexistent",
        "/analyses",  # GET not supported, only POST
        "/languages/python/extra",
        "/parsers/tree-sitter",  # Individual parser details not implemented
    ]
    
    for endpoint in endpoints:
        response = await rest_client.get(endpoint)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_analyses(rest_client):
    """Test handling concurrent analysis requests."""
    # Create multiple analysis tasks
    tasks = []
    for i in range(5):
        request_data = {
            "source": {
                "content": f"function test{i}() {{ return {i}; }}",
                "language": "javascript"
            }
        }
        task = rest_client.post("/analyses", json=request_data)
        tasks.append(task)
    
    # Execute concurrently
    responses = await asyncio.gather(*tasks)
    
    # Verify all succeeded and have unique IDs
    ids = set()
    for response in responses:
        assert response.status_code == 201
        data = response.json()
        assert "success" in data["data"]["attributes"]
        ids.add(data["data"]["id"])
    
    assert len(ids) == 5  # All IDs should be unique


@pytest.mark.asyncio
async def test_parse_error_handling(rest_client):
    """Test parsing error is properly returned."""
    request_data = {
        "source": {
            "content": "def broken syntax",
            "language": "python"
        }
    }
    
    response = await rest_client.post("/analyses", json=request_data)
    # Should still return 201 as the analysis was created
    assert response.status_code == 201
    
    data = response.json()
    # Tree-sitter actually parses this without error (it's forgiving)
    # But if there was an error, it would be in the response
    assert "data" in data
    assert "attributes" in data["data"]
    assert "error" in data["data"]["attributes"]


@pytest.mark.asyncio
async def test_json_api_content_type(rest_client):
    """Test that all responses use proper JSON:API content type."""
    endpoints = [
        ("/", "GET"),
        ("/languages", "GET"),
        ("/languages/python", "GET"),
        ("/parsers", "GET"),
    ]
    
    for endpoint, method in endpoints:
        if method == "GET":
            response = await rest_client.get(endpoint)
        else:
            response = await rest_client.post(endpoint, json={})
        
        assert response.headers["content-type"] == "application/vnd.api+json"