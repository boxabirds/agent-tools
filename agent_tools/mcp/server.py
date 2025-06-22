"""Simple MCP server implementation for agent-tools."""

import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict
from urllib.parse import urlparse, parse_qs

from agent_tools.api import AgentTools
from agent_tools.parsers.languages import LANGUAGE_CONFIGS

# Initialize tools
tools = AgentTools()
logger = logging.getLogger(__name__)


class MCPHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for MCP-like interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/health":
            self._send_json_response({
                "status": "healthy",
                "service": "agent-tools",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "0.1.0"
            })
        elif parsed_path.path == "/languages":
            languages = list(LANGUAGE_CONFIGS.keys())
            self._send_json_response({
                "languages": sorted(languages),
                "count": len(languages)
            })
        elif parsed_path.path == "/info":
            self._send_text_response(self._get_parser_info())
        else:
            self._send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_error(400, "No request body")
            return
            
        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_error(400, f"Invalid JSON: {str(e)}")
            return
        
        # Route to appropriate handler
        if parsed_path.path == "/parse":
            self._handle_parse_code(data)
        elif parsed_path.path == "/parse-file":
            self._handle_parse_file(data)
        elif parsed_path.path == "/check-language":
            self._handle_check_language(data)
        else:
            self._send_error(404, "Not found")
    
    def _handle_parse_code(self, data: Dict[str, Any]):
        """Handle code parsing request."""
        content = data.get('content')
        language = data.get('language')
        
        if not content or not language:
            self._send_error(400, "Missing required fields: content, language")
            return
        
        # Parse the code
        import asyncio
        result = asyncio.run(tools.parse_code(content, language))
        
        self._send_json_response({
            "success": result.success,
            "language": result.language,
            "ast": result.ast_text,
            "metadata": result.metadata,
            "error": result.error
        })
    
    def _handle_parse_file(self, data: Dict[str, Any]):
        """Handle file parsing request."""
        file_path = data.get('file_path')
        language = data.get('language')
        
        if not file_path:
            self._send_error(400, "Missing required field: file_path")
            return
        
        # Parse the file
        import asyncio
        result = asyncio.run(tools.parse_file(file_path, language))
        
        self._send_json_response({
            "success": result.success,
            "language": result.language,
            "ast": result.ast_text,
            "metadata": result.metadata,
            "error": result.error
        })
    
    def _handle_check_language(self, data: Dict[str, Any]):
        """Handle language availability check."""
        language = data.get('language')
        
        if not language:
            self._send_error(400, "Missing required field: language")
            return
        
        supported = language in LANGUAGE_CONFIGS
        
        # Check if grammar is available
        if supported:
            import asyncio
            from agent_tools.parsers.tree_sitter_parser import TreeSitterParser
            parser = TreeSitterParser()
            grammar_available = asyncio.run(parser.is_language_available(language))
        else:
            grammar_available = False
        
        self._send_json_response({
            "language": language,
            "supported": supported,
            "grammar_available": grammar_available,
            "message": f"Language {language} is {'supported' if supported else 'not supported'}"
        })
    
    def _get_parser_info(self) -> str:
        """Get parser information."""
        languages = sorted(LANGUAGE_CONFIGS.keys())
        return f"""Available parsers:
- tree-sitter

Supported languages:
{', '.join(languages)}

Total languages: {len(languages)}
"""
    
    def _send_json_response(self, data: Any, status: int = 200):
        """Send JSON response."""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def _send_text_response(self, text: str, status: int = 200):
        """Send text response."""
        response = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def _send_error(self, status: int, message: str):
        """Send error response."""
        self._send_json_response({"error": message}, status)
    
    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.info(format % args)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the MCP server."""
    server = HTTPServer((host, port), MCPHandler)
    print(f"Starting agent-tools MCP server on http://{host}:{port}")
    print("Available endpoints:")
    print("  GET  /health          - Health check")
    print("  GET  /languages       - List supported languages")
    print("  GET  /info           - Parser information")
    print("  POST /parse          - Parse code (content, language)")
    print("  POST /parse-file     - Parse file (file_path, language?)")
    print("  POST /check-language - Check language support (language)")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def main():
    """Entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Tools MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    run_server(args.host, args.port)