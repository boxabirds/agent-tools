#!/bin/bash
set -e

echo "Updating project metadata..."

# Update pyproject.toml
if [ -f "pyproject.toml" ]; then
    temp_file="pyproject.toml.tmp"
    sed 's/name = "mcpagenttools"/name = "mcp-code-parser"/g' pyproject.toml | \
    sed 's/agenttools = "agenttools.cli:main"/mcp-code-parser = "mcp_code_parser.cli:main"/g' | \
    sed 's/packages = \["agenttools", "agenttools.parsers", "agenttools.mcp", "agenttools.rest"\]/packages = ["mcp_code_parser", "mcp_code_parser.parsers"]/g' | \
    sed 's/version = {attr = "agenttools.__version__.__version__"}/version = {attr = "mcp_code_parser.__version__.__version__"}/g' | \
    sed 's|"Homepage" = "https://github.com/yourusername/mcpagenttools"|"Homepage" = "https://github.com/yourusername/mcp-code-parser"|g' | \
    sed 's|mcpagenttools|mcp-code-parser|g' | \
    sed 's/AI agent tools with tree-sitter based code parsing/MCP server for tree-sitter based code parsing/g' | \
    sed 's/"ai", "agents", "code-parsing", "tree-sitter", "ast", "mcp"/"mcp", "model-context-protocol", "code-parsing", "tree-sitter", "ast", "parser"/g' > "$temp_file"
    
    mv "$temp_file" pyproject.toml
    echo "  ✓ Updated pyproject.toml"
fi

# Update README.md
if [ -f "README.md" ]; then
    temp_file="README.md.tmp"
    sed 's/# agent-tools/# mcp-code-parser/g' README.md | \
    sed 's/# Agent-Tools/# MCP Code Parser/g' | \
    sed 's/# Agent Tools/# MCP Code Parser/g' | \
    sed 's/agent-tools/mcp-code-parser/g' | \
    sed 's/Agent-Tools/MCP Code Parser/g' | \
    sed 's/Agent Tools/MCP Code Parser/g' | \
    sed 's/agenttools/mcp_code_parser/g' | \
    sed 's/AI agents/MCP clients/g' | \
    sed 's/AI agent/MCP client/g' > "$temp_file"
    
    mv "$temp_file" README.md
    echo "  ✓ Updated README.md"
fi

# Update MANIFEST.in
if [ -f "MANIFEST.in" ]; then
    # No specific agenttools references in MANIFEST.in based on previous read
    echo "  ✓ MANIFEST.in (no changes needed)"
fi

# Update __version__.py
version_file="mcp_code_parser/__version__.py"
if [ ! -f "$version_file" ] && [ -f "agenttools/__version__.py" ]; then
    version_file="agenttools/__version__.py"
fi

if [ -f "$version_file" ]; then
    temp_file="${version_file}.tmp"
    sed 's/agenttools package/mcp-code-parser package/g' "$version_file" | \
    sed 's/AI agent tools with tree-sitter based code parsing/MCP server for tree-sitter based code parsing/g' > "$temp_file"
    
    mv "$temp_file" "$version_file"
    echo "  ✓ Updated __version__.py"
fi

# Update documentation files
for doc in docs/*.md; do
    if [ -f "$doc" ]; then
        temp_file="${doc}.tmp"
        sed 's/agent-tools/mcp-code-parser/g' "$doc" | \
        sed 's/Agent-Tools/MCP Code Parser/g' | \
        sed 's/Agent Tools/MCP Code Parser/g' | \
        sed 's/agenttools/mcp_code_parser/g' | \
        sed 's/AI agents/MCP clients/g' > "$temp_file"
        
        if ! cmp -s "$doc" "$temp_file"; then
            mv "$temp_file" "$doc"
            echo "  ✓ Updated: $doc"
        else
            rm "$temp_file"
        fi
    fi
done

echo "✓ Project metadata updated"