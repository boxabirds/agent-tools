# Project Restructuring Scripts

This directory contains scripts to rename the project from "agenttools" to "mcp-code-parser".

## Overview

The restructuring process:
1. Renames all directories and files
2. Updates all Python imports
3. Updates project metadata (pyproject.toml, README, etc.)
4. Removes REST API components (focusing on MCP only)
5. Streamlines the MCP structure
6. Validates all changes

## Scripts

### Main Script
- `rename_project.sh` - Orchestrates the entire renaming process

### Component Scripts
- `rename_directories.sh` - Renames directories and shell scripts
- `update_imports.sh` - Updates all Python imports and references
- `update_metadata.sh` - Updates project metadata files
- `remove_rest_components.sh` - Removes REST API related code
- `streamline_mcp.sh` - Simplifies MCP structure
- `validate_changes.sh` - Validates the restructuring

### Safety Scripts
- `rollback_changes.sh` - Restores from backup if something goes wrong

## Usage

1. **Review the scripts** to understand what changes will be made
2. **Ensure you're in the project root** (where `agenttools/` directory exists)
3. **Run the main script**:
   ```bash
   ./rename_project.sh
   ```

4. **After completion**, verify the changes:
   ```bash
   git status
   pytest  # Run tests
   ```

5. **If something goes wrong**, use the rollback:
   ```bash
   ./rollback_changes.sh
   ```

## What Gets Changed

### Directory Structure
- `agenttools/` → `mcp_code_parser/`
- `agenttools/mcp/server.py` → `mcp_code_parser/mcp_server.py`
- `agenttools/rest/` → (removed)

### Files Renamed
- `agent-tools-mcp.sh` → `mcp-code-parser.sh`
- `agent-tools-debug.sh` → `mcp-code-parser-debug.sh`

### Import Updates
- `from agenttools` → `from mcp_code_parser`
- `import agenttools` → `import mcp_code_parser`

### Package Metadata
- Package name: `mcpagenttools` → `mcp-code-parser`
- Description: Focused on MCP code parsing
- Removed REST API references

## Backup

The main script automatically creates a backup in the parent directory with timestamp:
- `../agent-tools-backup-YYYYMMDD-HHMMSS/`

## After Running

1. Update your git remote URL:
   ```bash
   git remote set-url origin https://github.com/yourusername/mcp-code-parser.git
   ```

2. Consider recreating your virtual environment with the new name:
   ```bash
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   ```

3. Clean up the restructuring scripts:
   ```bash
   rm rename_*.sh update_*.sh remove_*.sh streamline_*.sh validate_*.sh rollback_*.sh RESTRUCTURE_README.md
   ```