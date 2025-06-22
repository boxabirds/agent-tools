#!/bin/bash
# Debug wrapper for agent-tools MCP server

LOG_FILE="/tmp/agent-tools-mcp.log"
PROJECT_DIR="/Users/julian/expts/agent-tools"

echo "=== Agent Tools MCP Server Started at $(date) ===" >> "$LOG_FILE"
echo "Working directory: $(pwd)" >> "$LOG_FILE"
echo "Project directory: $PROJECT_DIR" >> "$LOG_FILE"
echo "Environment:" >> "$LOG_FILE"
env | grep -E "(PATH|PYTHON|UV)" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Redirect stderr to log file, but keep stdout clean for JSON-RPC
exec 2>>"$LOG_FILE"

echo "Starting MCP server with logging to $LOG_FILE" >&2
echo "Changed to directory: $(pwd)" >&2

# Find uv in common locations
if [ -x "$HOME/.pyenv/shims/uv" ]; then
    UV_CMD="$HOME/.pyenv/shims/uv"
elif command -v uv &> /dev/null; then
    UV_CMD="uv"
elif [ -x "/usr/local/bin/uv" ]; then
    UV_CMD="/usr/local/bin/uv"
elif [ -x "$HOME/.cargo/bin/uv" ]; then
    UV_CMD="$HOME/.cargo/bin/uv"
else
    echo "ERROR: uv not found in PATH" >&2
    exit 1
fi

echo "Using uv at: $UV_CMD" >&2

# Run the actual server
"$UV_CMD" run agent-tools serve