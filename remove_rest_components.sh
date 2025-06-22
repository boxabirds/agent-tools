#!/bin/bash
set -e

echo "Removing REST API components..."

# Remove REST directory
if [ -d "mcp_code_parser/rest" ] || [ -d "agenttools/rest" ]; then
    if [ -d "mcp_code_parser/rest" ]; then
        rm -rf mcp_code_parser/rest
        echo "  ✓ Removed mcp_code_parser/rest/"
    elif [ -d "agenttools/rest" ]; then
        rm -rf agenttools/rest
        echo "  ✓ Removed agenttools/rest/"
    fi
fi

# Remove REST-related test files
rest_tests=(
    "tests/test_rest_server.py"
)

for test_file in "${rest_tests[@]}"; do
    if [ -f "$test_file" ]; then
        rm "$test_file"
        echo "  ✓ Removed $test_file"
    fi
done

# Remove REST API documentation
if [ -f "docs/openapi.yaml" ]; then
    rm docs/openapi.yaml
    echo "  ✓ Removed docs/openapi.yaml"
fi

# Update pyproject.toml to remove httpx dependency (REST-specific)
if [ -f "pyproject.toml" ]; then
    temp_file="pyproject.toml.tmp"
    grep -v '"httpx>=' pyproject.toml > "$temp_file" || true
    mv "$temp_file" pyproject.toml
    echo "  ✓ Removed httpx dependency from pyproject.toml"
fi

# Remove REST-related example files
if [ -f "examples/rest_client.py" ]; then
    rm examples/rest_client.py
    echo "  ✓ Removed examples/rest_client.py"
fi

echo "✓ REST API components removed"