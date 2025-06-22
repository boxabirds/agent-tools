#!/bin/bash
set -e

echo "Renaming directories..."

# Rename main package directory
if [ -d "mcp_code_parser" ]; then
    git mv mcp_code_parser mcp_code_parser
    echo "✓ Renamed mcp_code_parser/ to mcp_code_parser/"
else
    echo "⚠ mcp_code_parser directory not found, may already be renamed"
fi

# Remove old egg-info if exists
if [ -d "mcp_code_parser.egg-info" ]; then
    rm -rf mcp_code_parser.egg-info
    echo "✓ Removed old mcp_code_parser.egg-info"
fi

# Rename shell scripts
if [ -f "mcp-code-parser-mcp.sh" ]; then
    git mv mcp-code-parser-mcp.sh mcp-code-parser.sh
    echo "✓ Renamed mcp-code-parser-mcp.sh to mcp-code-parser.sh"
fi

if [ -f "mcp-code-parser-debug.sh" ]; then
    git mv mcp-code-parser-debug.sh mcp-code-parser-debug.sh
    echo "✓ Renamed mcp-code-parser-debug.sh to mcp-code-parser-debug.sh"
fi

echo "✓ Directory renaming complete"