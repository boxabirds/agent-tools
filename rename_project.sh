#!/bin/bash
set -e

# Main orchestration script for renaming project from mcp_code_parser to mcp-code-parser

echo "=== Starting project rename from mcp_code_parser to mcp-code-parser ==="
echo ""

# Check if we're in the right directory
if [ ! -d "mcp_code_parser" ]; then
    echo "Error: mcp_code_parser directory not found. Are you in the project root?"
    exit 1
fi

# Create backup
echo "Creating backup..."
BACKUP_DIR="../mcp-code-parser-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✓ Backup created at: $BACKUP_DIR"
echo ""

# Run rename scripts in order
echo "Step 1: Renaming directories..."
bash ./rename_directories.sh
echo ""

echo "Step 2: Updating Python imports..."
bash ./update_imports.sh
echo ""

echo "Step 3: Updating project metadata..."
bash ./update_metadata.sh
echo ""

echo "Step 4: Cleaning up REST API components..."
bash ./remove_rest_components.sh
echo ""

echo "Step 5: Streamlining MCP structure..."
bash ./streamline_mcp.sh
echo ""

echo "Step 6: Validating changes..."
bash ./validate_changes.sh
echo ""

echo "=== Project rename completed! ==="
echo ""
echo "Next steps:"
echo "1. Review the changes with: git status"
echo "2. Run tests with: pytest"
echo "3. Update git remote URL to match new name"
echo "4. Consider updating virtual environment name"