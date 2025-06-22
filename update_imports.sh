#!/bin/bash
set -e

echo "Updating Python imports..."

# Function to update imports in a file
update_file() {
    local file="$1"
    local temp_file="${file}.tmp"
    
    # Skip backup files
    if [[ "$file" == *.bak ]]; then
        return
    fi
    
    # Create temp file with updated imports
    sed 's/from agenttools/from mcp_code_parser/g' "$file" | \
    sed 's/import agenttools/import mcp_code_parser/g' | \
    sed 's/agenttools\./mcp_code_parser./g' | \
    sed 's/"agenttools"/"mcp_code_parser"/g' | \
    sed "s/'agenttools'/'mcp_code_parser'/g" > "$temp_file"
    
    # Only update if changes were made
    if ! cmp -s "$file" "$temp_file"; then
        mv "$temp_file" "$file"
        echo "  ✓ Updated: $file"
    else
        rm "$temp_file"
    fi
}

# Find all Python files and update them
find . -type f -name "*.py" -not -path "./venv/*" -not -path "./.git/*" -not -path "./agent_tools.egg-info/*" -not -path "./*.egg-info/*" | while read -r file; do
    update_file "$file"
done

echo "✓ Python imports updated"

echo ""
echo "Updating shell scripts..."

# Update shell scripts
for script in *.sh test_mcp_manual.sh; do
    if [ -f "$script" ]; then
        temp_file="${script}.tmp"
        sed 's/agenttools/mcp_code_parser/g' "$script" | \
        sed 's/agent-tools/mcp-code-parser/g' | \
        sed 's/agent_tools/mcp_code_parser/g' > "$temp_file"
        
        if ! cmp -s "$script" "$temp_file"; then
            mv "$temp_file" "$script"
            echo "  ✓ Updated: $script"
        else
            rm "$temp_file"
        fi
    fi
done

echo "✓ Shell scripts updated"