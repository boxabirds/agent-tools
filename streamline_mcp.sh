#!/bin/bash
set -e

echo "Streamlining MCP structure..."

# Check which directory exists
if [ -d "mcp_code_parser/mcp" ]; then
    MCP_DIR="mcp_code_parser/mcp"
    PARENT_DIR="mcp_code_parser"
elif [ -d "mcp_code_parser/mcp" ]; then
    MCP_DIR="mcp_code_parser/mcp"
    PARENT_DIR="mcp_code_parser"
else
    echo "  ⚠ No MCP directory found, skipping streamlining"
    exit 0
fi

# Move server.py to parent directory
if [ -f "$MCP_DIR/server.py" ]; then
    mv "$MCP_DIR/server.py" "$PARENT_DIR/mcp_server.py"
    echo "  ✓ Moved $MCP_DIR/server.py to $PARENT_DIR/mcp_server.py"
fi

# Move http_server.py if needed
if [ -f "$MCP_DIR/http_server.py" ]; then
    mv "$MCP_DIR/http_server.py" "$PARENT_DIR/mcp_http_server.py"
    echo "  ✓ Moved $MCP_DIR/http_server.py to $PARENT_DIR/mcp_http_server.py"
fi

# Remove the now-empty mcp directory
if [ -d "$MCP_DIR" ]; then
    rm -rf "$MCP_DIR"
    echo "  ✓ Removed $MCP_DIR directory"
fi

# Update imports in moved files
if [ -f "$PARENT_DIR/mcp_server.py" ]; then
    temp_file="$PARENT_DIR/mcp_server.py.tmp"
    sed 's/from mcp_code_parser import/from . import/g' "$PARENT_DIR/mcp_server.py" | \
    sed 's/from mcp_code_parser.parsers/from .parsers/g' > "$temp_file"
    mv "$temp_file" "$PARENT_DIR/mcp_server.py"
    echo "  ✓ Updated imports in mcp_server.py"
fi

# Update test imports
for test_file in tests/test_mcp*.py; do
    if [ -f "$test_file" ]; then
        temp_file="${test_file}.tmp"
        sed 's/mcp_code_parser.mcp.server/mcp_code_parser.mcp_server/g' "$test_file" | \
        sed 's/mcp_code_parser.mcp.http_server/mcp_code_parser.mcp_http_server/g' > "$temp_file"
        
        if ! cmp -s "$test_file" "$temp_file"; then
            mv "$temp_file" "$test_file"
            echo "  ✓ Updated imports in $test_file"
        else
            rm "$temp_file"
        fi
    fi
done

# Update CLI imports if they reference MCP
if [ -f "$PARENT_DIR/cli.py" ]; then
    temp_file="$PARENT_DIR/cli.py.tmp"
    sed 's/\.mcp\.server/.mcp_server/g' "$PARENT_DIR/cli.py" | \
    sed 's/\.mcp\.http_server/.mcp_http_server/g' > "$temp_file"
    
    if ! cmp -s "$PARENT_DIR/cli.py" "$temp_file"; then
        mv "$temp_file" "$PARENT_DIR/cli.py"
        echo "  ✓ Updated imports in cli.py"
    else
        rm "$temp_file"
    fi
fi

echo "✓ MCP structure streamlined"