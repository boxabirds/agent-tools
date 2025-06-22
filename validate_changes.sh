#!/bin/bash
set -e

echo "Validating changes..."

# Counter for issues found
issues=0

# Check for remaining mcp_code_parser references
echo ""
echo "Checking for remaining 'mcp_code_parser' references..."
mcp_code_parser_count=$(grep -r "mcp_code_parser" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | wc -l || echo "0")

if [ "$mcp_code_parser_count" -gt 0 ]; then
    echo "  ⚠ Found $mcp_code_parser_count remaining 'mcp_code_parser' references:"
    grep -r "mcp_code_parser" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | head -10 || true
    issues=$((issues + 1))
else
    echo "  ✓ No 'mcp_code_parser' references found"
fi

# Check for remaining mcp-code-parser references
echo ""
echo "Checking for remaining 'mcp-code-parser' references..."
mcp_code_parser_count=$(grep -r "mcp-code-parser" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | wc -l || echo "0")

if [ "$mcp_code_parser_count" -gt 0 ]; then
    echo "  ⚠ Found $mcp_code_parser_count remaining 'mcp-code-parser' references:"
    grep -r "mcp-code-parser" . --include="*.py" --include="*.md" --include="*.sh" --include="*.toml" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir="*.egg-info" --exclude="rename_*.sh" --exclude="update_*.sh" --exclude="streamline_*.sh" --exclude="validate_*.sh" --exclude="remove_*.sh" 2>/dev/null | head -10 || true
    issues=$((issues + 1))
else
    echo "  ✓ No 'mcp-code-parser' references found"
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
if [ -d "mcp_code_parser" ]; then
    echo "  ⚠ Old 'mcp_code_parser' directory still exists!"
    issues=$((issues + 1))
else
    echo "  ✓ Old 'mcp_code_parser' directory removed"
fi

# Check for REST components
echo ""
echo "Checking REST components removal..."
if [ -d "mcp_code_parser/rest" ] || [ -d "mcp_code_parser/rest" ]; then
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