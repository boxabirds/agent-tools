#!/bin/bash
set -e

echo "=== Rolling back changes ==="
echo ""

# This script helps rollback changes if something goes wrong
# It assumes you have a backup directory created by rename_project.sh

# Find the most recent backup
BACKUP_DIR=$(ls -dt ../agent-tools-backup-* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "Error: No backup directory found!"
    echo "Expected backup directories in parent directory named 'agent-tools-backup-*'"
    exit 1
fi

echo "Found backup: $BACKUP_DIR"
echo ""
read -p "Are you sure you want to restore from this backup? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled."
    exit 0
fi

# Save current state just in case
FAILED_DIR="../mcp-code-parser-failed-$(date +%Y%m%d-%H%M%S)"
echo "Saving current state to: $FAILED_DIR"
cd ..
mv agent-tools "$FAILED_DIR" 2>/dev/null || mv mcp-code-parser "$FAILED_DIR"

# Restore from backup
echo "Restoring from backup..."
cp -r "$BACKUP_DIR" agent-tools

cd agent-tools
echo ""
echo "✓ Rollback complete!"
echo ""
echo "The failed attempt has been saved to: $FAILED_DIR"
echo "You can safely delete it once you've verified the rollback."