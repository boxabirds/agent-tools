#!/bin/bash
set -e

echo "Validating changes..."

# Counter for issues found
issues=0

# Check for remaining agenttools references
echo ""
echo "Checking for remaining 'agenttools' references..."
agenttools_count=$(grep -r "agenttools" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | wc -l || echo "0")

if [ "$agenttools_count" -gt 0 ]; then
    echo "  ⚠ Found $agenttools_count remaining 'agenttools' references:"
    grep -r "agenttools" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | head -10 || true
    issues=$((issues + 1))
else
    echo "  ✓ No 'agenttools' references found"
fi

# Check for remaining agent-tools references
echo ""
echo "Checking for remaining 'agent-tools' references..."
agent_tools_count=$(grep -r "agent-tools" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | wc -l || echo "0")

if [ "$agent_tools_count" -gt 0 ]; then
    echo "  ⚠ Found $agent_tools_count remaining 'agent-tools' references:"
    grep -r "agent-tools" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | head -10 || true
    issues=$((issues + 1))
else
    echo "  ✓ No 'agent-tools' references found"
fi

# Check if main package directory exists
echo ""
echo "Checking package structure..."
if [ -d "mcp_code_parser" ]; then
    echo "  ✓ mcp_code_parser directory exists"
else
    echo "  ⚠ mcp_code_parser directory not found!"
    issues=$((issues + 1))
fi

# Check if old directory still exists
if [ -d "agenttools" ]; then
    echo "  ⚠ Old 'agenttools' directory still exists!"
    issues=$((issues + 1))
else
    echo "  ✓ Old 'agenttools' directory removed"
fi

# Check for REST components
echo ""
echo "Checking REST components removal..."
if [ -d "mcp_code_parser/rest" ] || [ -d "agenttools/rest" ]; then
    echo "  ⚠ REST directory still exists!"
    issues=$((issues + 1))
else
    echo "  ✓ REST directory removed"
fi

if [ -f "tests/test_rest_server.py" ]; then
    echo "  ⚠ test_rest_server.py still exists!"
    issues=$((issues + 1))
else
    echo "  ✓ REST tests removed"
fi

# Try a basic import test
echo ""
echo "Testing basic imports..."
if [ -d "mcp_code_parser" ]; then
    python -c "import sys; sys.path.insert(0, '.'); import mcp_code_parser" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✓ Basic import successful"
    else
        echo "  ⚠ Basic import failed"
        issues=$((issues + 1))
    fi
fi

# Summary
echo ""
echo "====================================="
if [ $issues -eq 0 ]; then
    echo "✓ Validation complete! No issues found."
    echo ""
    echo "The project has been successfully renamed to mcp-code-parser."
else
    echo "⚠ Validation found $issues issue(s)."
    echo ""
    echo "Please review the issues above and fix them manually if needed."
fi
echo "====================================="

exit $issues