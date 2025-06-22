#!/bin/bash
set -e

echo "Renaming directories..."

# Rename main package directory
if [ -d "agenttools" ]; then
    git mv agenttools mcp_code_parser
    echo "✓ Renamed agenttools/ to mcp_code_parser/"
else
    echo "⚠ agenttools directory not found, may already be renamed"
fi

# Remove old egg-info if exists
if [ -d "agent_tools.egg-info" ]; then
    rm -rf agent_tools.egg-info
    echo "✓ Removed old agent_tools.egg-info"
fi

# Rename shell scripts
if [ -f "agent-tools-mcp.sh" ]; then
    git mv agent-tools-mcp.sh mcp-code-parser.sh
    echo "✓ Renamed agent-tools-mcp.sh to mcp-code-parser.sh"
fi

if [ -f "agent-tools-debug.sh" ]; then
    git mv agent-tools-debug.sh mcp-code-parser-debug.sh
    echo "✓ Renamed agent-tools-debug.sh to mcp-code-parser-debug.sh"
fi

echo "✓ Directory renaming complete"