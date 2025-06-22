#!/bin/bash

# Test MCP server with proper protocol sequence

# Create a named pipe for bidirectional communication
mkfifo /tmp/mcp_in /tmp/mcp_out 2>/dev/null || true

# Start the MCP server in background
uv run agent-tools serve < /tmp/mcp_in > /tmp/mcp_out 2>&1 &
MCP_PID=$!

# Function to send request and read response
send_request() {
    echo "$1" > /tmp/mcp_in
    head -n1 /tmp/mcp_out
}

# Initialize
echo "=== Initializing MCP connection ==="
INIT_REQ='{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test-client","version":"1.0"}}}'
echo "$INIT_REQ" > /tmp/mcp_in
INIT_RESP=$(head -n1 /tmp/mcp_out)
echo "Response: $INIT_RESP"
echo

# Send initialized notification
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}' > /tmp/mcp_in

# List tools
echo "=== Listing available tools ==="
LIST_REQ='{"jsonrpc":"2.0","method":"tools/list","id":2,"params":{}}'
echo "$LIST_REQ" > /tmp/mcp_in
LIST_RESP=$(head -n1 /tmp/mcp_out)
echo "Response: $LIST_RESP" | jq -r '.result.tools[].name' 2>/dev/null || echo "$LIST_RESP"
echo

# Parse some code
echo "=== Parsing Python code ==="
PARSE_REQ='{"jsonrpc":"2.0","method":"tools/call","id":3,"params":{"name":"parse_code","arguments":{"content":"def hello():\n    return \"world\"","language":"python"}}}'
echo "$PARSE_REQ" > /tmp/mcp_in
PARSE_RESP=$(head -n1 /tmp/mcp_out)
echo "Response: $PARSE_RESP" | jq -r '.result.content[0].text' 2>/dev/null | jq . 2>/dev/null || echo "$PARSE_RESP"

# Cleanup
kill $MCP_PID 2>/dev/null
rm -f /tmp/mcp_in /tmp/mcp_out