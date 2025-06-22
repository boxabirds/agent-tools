#!/bin/bash
# Production MCP server launcher for agent-tools

PROJECT_DIR="/Users/julian/expts/agent-tools"
UV_CMD="$HOME/.pyenv/shims/uv"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Run with specified log level (can be overridden with AGENT_TOOLS_LOG_LEVEL env var)
LOG_LEVEL="${AGENT_TOOLS_LOG_LEVEL:-INFO}"

# Run the MCP server
exec "$UV_CMD" run agent-tools serve --log-level "$LOG_LEVEL"