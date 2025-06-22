"""RESTful API server implementation for agent-tools."""

import importlib
import json
import uuid
import logging
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse, parse_qs
from collections import OrderedDict
import re

from agenttools.api import AgentTools
from agenttools.parsers.languages import LANGUAGE_CONFIGS
from agenttools.parsers.tree_sitter import TreeSitterParser

# Pre-import language modules to ensure they're available
try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go
except ImportError:
    pass  # Optional languages may not be installed

# Initialize tools
tools = AgentTools()
logger = logging.getLogger(__name__)

# In-memory cache for analyses (in production, use Redis or similar)
# Using OrderedDict for LRU-style cache
analyses_cache = OrderedDict()
MAX_CACHE_SIZE = 100


class RESTHandler(BaseHTTPRequestHandler):
    """RESTful HTTP handler for agent-tools API."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path_parts = [p for p in parsed_path.path.split('/') if p]
        
        # Route handling
        if not path_parts:
            # GET / - API root
            self._send_api_root()
        elif path_parts[0] == 'analyses' and len(path_parts) == 2:
            # GET /analyses/{id}
            self._get_analysis(path_parts[1])
        elif path_parts[0] == 'languages':
            if len(path_parts) == 1:
                # GET /languages
                self._list_languages()
            elif len(path_parts) == 2:
                # GET /languages/{id}
                self._get_language(path_parts[1])
            else:
                self._send_error(404, "Not found")
        elif path_parts[0] == 'parsers':
            if len(path_parts) == 1:
                # GET /parsers
                self._list_parsers()
            else:
                self._send_error(404, "Not found")
        elif path_parts[0] == 'openapi.yaml':
            # GET /openapi.yaml - Serve OpenAPI spec
            self._serve_openapi_spec()
        else:
            self._send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path_parts = [p for p in parsed_path.path.split('/') if p]
        
        if path_parts == ['analyses']:
            # POST /analyses
            self._create_analysis()
        else:
            self._send_error(404, "Not found")
    
    def _send_api_root(self):
        """Send API root with available endpoints."""
        response = {
            "data": {
                "type": "api",
                "id": "agent-tools-rest-api",
                "attributes": {
                    "version": "1.0.0",
                    "description": "RESTful API for agent-tools code parsing"
                },
                "links": {
                    "self": "/",
                    "analyses": "/analyses",
                    "languages": "/languages",
                    "parsers": "/parsers",
                    "openapi": "/openapi.yaml"
                }
            }
        }
        self._send_json_response(response)
    
    def _create_analysis(self):
        """Create a new code analysis."""
        # Read and parse request body
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "No request body")
                return
                
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_error(400, f"Invalid JSON: {str(e)}")
            return
        
        # Validate request structure
        if 'source' not in data:
            self._send_error(400, "Missing required field: source")
            return
        
        source = data['source']
        
        # Determine if it's content or file parsing
        if 'content' in source:
            content = source['content']
            language = source.get('language')
            file_path = None
            
            if not language:
                self._send_error(400, "Language is required when providing content")
                return
                
            # Parse the code
            import asyncio
            result = asyncio.run(tools.parse_code(content, language))
            
        elif 'file_path' in source:
            file_path = source['file_path']
            language = source.get('language')  # Optional for files
            
            # Parse the file
            import asyncio
            result = asyncio.run(tools.parse_file(file_path, language))
            
        else:
            self._send_error(400, "Source must contain either 'content' or 'file_path'")
            return
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        
        # Create response
        analysis_data = {
            "id": analysis_id,
            "type": "analysis",
            "attributes": {
                "language": result.language,
                "parser": "tree-sitter",
                "success": result.success,
                "ast": result.ast_text if result.success else None,
                "error": result.error,
                "metadata": result.metadata,
                "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            },
            "relationships": {
                "language": {
                    "data": {"type": "language", "id": result.language}
                },
                "parser": {
                    "data": {"type": "parser", "id": "tree-sitter"}
                }
            },
            "links": {
                "self": f"/analyses/{analysis_id}"
            }
        }
        
        # Cache the analysis
        self._cache_analysis(analysis_id, analysis_data)
        
        # Send response with 201 Created
        response = {"data": analysis_data}
        response_json = json.dumps(response, indent=2).encode('utf-8')
        
        self.send_response(201)
        self.send_header('Content-Type', 'application/vnd.api+json')
        self.send_header('Content-Length', str(len(response_json)))
        self.send_header('Location', f'/analyses/{analysis_id}')
        self.end_headers()
        self.wfile.write(response_json)
    
    def _get_analysis(self, analysis_id: str):
        """Retrieve a specific analysis."""
        if analysis_id in analyses_cache:
            response = {"data": analyses_cache[analysis_id]}
            # Move to end to mark as recently used
            analyses_cache.move_to_end(analysis_id)
            self._send_json_response(response)
        else:
            self._send_error(404, f"Analysis {analysis_id} not found")
    
    def _list_languages(self):
        """List all supported languages."""
        languages_data = []
        
        for lang_id in sorted(LANGUAGE_CONFIGS.keys()):
            config = LANGUAGE_CONFIGS[lang_id]
            languages_data.append({
                "id": lang_id,
                "type": "language",
                "attributes": {
                    "name": lang_id.title(),
                    "file_extensions": config.file_extensions,
                    "available": self._check_language_availability(lang_id)
                },
                "links": {
                    "self": f"/languages/{lang_id}"
                }
            })
        
        response = {
            "data": languages_data,
            "meta": {
                "total": len(languages_data)
            }
        }
        self._send_json_response(response)
    
    def _get_language(self, language_id: str):
        """Get details about a specific language."""
        if language_id not in LANGUAGE_CONFIGS:
            self._send_error(404, f"Language {language_id} not found")
            return
        
        config = LANGUAGE_CONFIGS[language_id]
        available = self._check_language_availability(language_id)
        
        response = {
            "data": {
                "id": language_id,
                "type": "language",
                "attributes": {
                    "name": language_id.title(),
                    "file_extensions": config.file_extensions,
                    "available": available,
                    "package_name": f"tree-sitter-{language_id}",
                    "node_types": {
                        "included": list(config.node_types_to_include) if config.node_types_to_include else [],
                        "excluded": list(config.node_types_to_exclude) if config.node_types_to_exclude else []
                    }
                },
                "links": {
                    "self": f"/languages/{language_id}"
                }
            }
        }
        self._send_json_response(response)
    
    def _list_parsers(self):
        """List available parsers."""
        parsers_data = [{
            "id": "tree-sitter",
            "type": "parser",
            "attributes": {
                "name": "Tree-sitter",
                "version": "0.20.0+",
                "description": "Fast, incremental parsing library with support for multiple languages",
                "supported_languages": sorted(LANGUAGE_CONFIGS.keys())
            },
            "links": {
                "self": "/parsers/tree-sitter"
            }
        }]
        
        response = {
            "data": parsers_data,
            "meta": {
                "total": len(parsers_data)
            }
        }
        self._send_json_response(response)
    
    def _serve_openapi_spec(self):
        """Serve the OpenAPI specification."""
        # In a real implementation, we'd read from a file
        # For now, send a simple response indicating where to find it
        self._send_text_response(
            "OpenAPI specification will be available here. See /docs/openapi.yaml",
            content_type="text/plain"
        )
    
    def _check_language_availability(self, language: str) -> bool:
        """Check if a language grammar is available."""
        try:
            # Simple check - try to import the language module
            module_name = f"tree_sitter_{language}"
            importlib.import_module(module_name)
            logger.debug(f"Language {language} is available (module {module_name} found)")
            return True
        except ImportError as e:
            logger.debug(f"Language {language} is not available: {e}")
            return False
    
    def _cache_analysis(self, analysis_id: str, analysis_data: dict):
        """Cache an analysis, maintaining size limit."""
        analyses_cache[analysis_id] = analysis_data
        
        # Remove oldest if over limit
        if len(analyses_cache) > MAX_CACHE_SIZE:
            analyses_cache.popitem(last=False)
    
    def _send_json_response(self, data: Any, status: int = 200):
        """Send JSON:API formatted response."""
        response = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/vnd.api+json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def _send_text_response(self, text: str, status: int = 200, content_type: str = "text/plain"):
        """Send text response."""
        response = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def _send_error(self, status: int, message: str):
        """Send JSON:API error response."""
        error_response = {
            "errors": [{
                "status": str(status),
                "title": self.responses.get(status, ['Unknown Error'])[0],
                "detail": message
            }]
        }
        self._send_json_response(error_response, status)
    
    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.info(format % args)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the RESTful API server."""
    server = HTTPServer((host, port), RESTHandler)
    print(f"Starting agent-tools RESTful API server on http://{host}:{port}")
    print("API Documentation:")
    print("  GET  /                      - API root")
    print("  GET  /languages             - List supported languages")
    print("  GET  /languages/{id}        - Get language details")
    print("  GET  /parsers               - List available parsers")
    print("  POST /analyses              - Create new analysis")
    print("  GET  /analyses/{id}         - Get analysis result")
    print("  GET  /openapi.yaml          - OpenAPI specification")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def main():
    """Entry point for REST server."""
    import argparse
    parser = argparse.ArgumentParser(description="Run agent-tools RESTful API server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    args = parser.parse_args()
    
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()