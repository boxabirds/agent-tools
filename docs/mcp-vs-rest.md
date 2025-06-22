# MCP vs RESTful API: A Comparison

This document explains the differences between the Model Context Protocol (MCP) and RESTful API interfaces provided by agent-tools, helping you choose the right one for your use case.

## Overview

Agent-tools provides two different API interfaces:
- **MCP (Model Context Protocol)**: For MCP clients and tools that support MCP
- **RESTful API**: For traditional HTTP-based integrations

Both interfaces expose the same core functionality but differ significantly in their approach and capabilities.

## Protocol Differences

### MCP (Model Context Protocol)

**Protocol**: JSON-RPC 2.0 over stdio or Server-Sent Events (SSE)
- Bidirectional communication
- Stateful sessions with initialization handshake
- Request/response with unique IDs

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "parse_code",
    "arguments": {
      "content": "def hello(): pass",
      "language": "python"
    }
  },
  "id": 1
}
```

### RESTful API

**Protocol**: HTTP with JSON payloads
- Unidirectional request/response
- Stateless - each request is independent
- Standard HTTP methods and status codes

**Example Request**:
```http
POST /analyses
Content-Type: application/vnd.api+json

{
  "source": {
    "content": "def hello(): pass",
    "language": "python"
  }
}
```

## Feature Comparison

| Feature | MCP | RESTful API |
|---------|-----|-------------|
| **Discovery** | Dynamic tool discovery via `tools/list` | Static endpoints, OpenAPI documentation |
| **State Management** | Stateful sessions | Stateless requests |
| **Communication** | Bidirectional (server can send notifications) | Request/response only |
| **Streaming** | Built-in support | Requires SSE/WebSockets |
| **Type Information** | Schemas included in protocol | Separate OpenAPI spec |
| **Cancellation** | Built-in support | Client-side only |
| **Progress Updates** | Native support | Requires polling or SSE |
| **Caching** | Client-managed | Server-side with ETags |

## API Capabilities

### MCP Exclusive Features

1. **Tool Discovery**
   - List available tools dynamically
   - Get tool schemas and descriptions
   - No hardcoded endpoints needed

2. **Resource Management**
   - List available resources
   - Subscribe to resource changes
   - Template-based resource URIs

3. **Prompts**
   - Pre-defined prompt templates
   - Dynamic prompt generation
   - Context-aware completions

4. **Session Context**
   - Maintain conversation state
   - Share context between calls
   - Progress notifications

### RESTful API Exclusive Features

1. **Standard HTTP**
   - Works with any HTTP client
   - Standard caching mechanisms
   - Load balancer friendly

2. **Resource-Oriented**
   - Predictable URLs
   - CRUD operations
   - Hypermedia links (HATEOAS)

3. **Stateless Scaling**
   - Horizontal scaling
   - No session affinity needed
   - Standard HTTP caching

## Use Case Recommendations

### Use MCP When:

- Building MCP clients or assistants
- Using Claude Desktop, Cursor, or Windsurf
- Need dynamic tool discovery
- Want bidirectional communication
- Require progress updates or streaming
- Building conversational interfaces

### Use RESTful API When:

- Building traditional web applications
- Integrating with existing HTTP infrastructure
- Need stateless, scalable architecture
- Want to use standard HTTP tooling
- Building microservices
- Need fine-grained caching control

## Example: Same Operation, Different Protocols

### Parsing Python Code

**MCP Approach**:
```json
// 1. Initialize connection
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  },
  "id": 1
}

// 2. Discover tools
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}

// 3. Call parse tool
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "parse_code",
    "arguments": {
      "content": "def hello(): pass",
      "language": "python"
    }
  },
  "id": 3
}
```

**RESTful Approach**:
```http
// Single request
POST /analyses
Content-Type: application/vnd.api+json

{
  "source": {
    "content": "def hello(): pass",
    "language": "python"
  }
}

// Response includes self-link for future retrieval
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "analysis",
    "attributes": {
      "language": "python",
      "ast": "module\n  function_definition...",
      "success": true
    },
    "links": {
      "self": "/analyses/550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

## Performance Considerations

### MCP
- Lower latency for multiple operations (persistent connection)
- Higher memory usage (session state)
- Better for interactive/conversational use

### RESTful
- Higher latency per request (connection overhead)
- Lower memory usage (stateless)
- Better for batch processing and microservices

## Security Considerations

### MCP
- Typically runs locally (stdio) or over secure channels
- Authentication at session level
- Limited attack surface

### RESTful
- Standard HTTP security (HTTPS, OAuth, API keys)
- Per-request authentication
- Well-understood security model

## Conclusion

Choose **MCP** for AI agent integrations and interactive tools that benefit from stateful sessions and dynamic discovery.

Choose **RESTful API** for traditional web applications, microservices, and scenarios requiring standard HTTP infrastructure and stateless scaling.

Both APIs provide access to the same powerful tree-sitter parsing capabilities - the choice depends on your specific integration requirements and architecture.