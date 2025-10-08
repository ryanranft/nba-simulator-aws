#!/bin/bash
#
# Save Work Context
# Saves the current work state to allow resuming after scraper check
#
# Usage:
#   bash scripts/monitoring/save_work_context.sh "Task description" "Current step" "Next step"
#

set -e

CONTEXT_FILE="/tmp/claude_work_context.json"

task_description="${1:-Unknown task}"
current_step="${2:-In progress}"
next_step="${3:-To be determined}"

# Create context file
cat > "$CONTEXT_FILE" <<EOF
{
  "task": "$task_description",
  "current_step": "$current_step",
  "next_step": "$next_step",
  "timestamp": "$(date '+%Y-%m-%d %H:%M:%S')",
  "files_in_progress": []
}
EOF

echo "✅ Work context saved to $CONTEXT_FILE"