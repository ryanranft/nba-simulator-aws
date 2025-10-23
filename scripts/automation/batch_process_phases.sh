#!/bin/bash
#
# Batch Process Phases - Shell Wrapper
#
# Convenience wrapper for autonomous_phase_completion.py
#
# Usage:
#   bash scripts/automation/batch_process_phases.sh --all
#   bash scripts/automation/batch_process_phases.sh --phase 0
#   bash scripts/automation/batch_process_phases.sh --all --dry-run
#
# Author: Claude Code
# Created: October 23, 2025

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." && pwd )"

echo "=================================================="
echo "Autonomous Phase Completion - Batch Processor"
echo "=================================================="
echo ""
echo "Project Root: ${PROJECT_ROOT}"
echo ""

# Check if Python script exists
PYTHON_SCRIPT="${PROJECT_ROOT}/scripts/automation/autonomous_phase_completion.py"
if [ ! -f "${PYTHON_SCRIPT}" ]; then
    echo -e "${RED}❌ Error: autonomous_phase_completion.py not found${NC}"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: ${PYTHON_VERSION}"
echo ""

# Parse arguments
ARGS="$@"

# Show what we're doing
if [[ "$ARGS" == *"--dry-run"* ]]; then
    echo -e "${YELLOW}🔍 Running in DRY RUN mode${NC}"
else:
    echo -e "${GREEN}🚀 Running in LIVE mode${NC}"
fi

if [[ "$ARGS" == *"--all"* ]]; then
    echo "Processing all phases (0-9)"
elif [[ "$ARGS" == *"--phase"* ]]; then
    PHASE_NUM=$(echo "$ARGS" | grep -oP '(?<=--phase )\d+')
    echo "Processing Phase ${PHASE_NUM}"
else
    echo -e "${RED}❌ Error: Must specify --all or --phase N${NC}"
    echo ""
    echo "Usage:"
    echo "  bash scripts/automation/batch_process_phases.sh --all"
    echo "  bash scripts/automation/batch_process_phases.sh --phase 0"
    echo "  bash scripts/automation/batch_process_phases.sh --all --dry-run"
    exit 1
fi

echo ""
echo "=================================================="
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Run Python script
echo "Launching autonomous agent..."
echo ""

python3 "${PYTHON_SCRIPT}" ${ARGS}

EXIT_CODE=$?

echo ""
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Autonomous agent completed successfully${NC}"
else
    echo -e "${RED}❌ Autonomous agent failed with exit code ${EXIT_CODE}${NC}"
fi
echo "=================================================="
echo ""

# Show summary location
if [ -f "${PROJECT_ROOT}/PHASE_COMPLETION_SUMMARY.md" ]; then
    echo "📄 Summary report: PHASE_COMPLETION_SUMMARY.md"
fi

if [ -f "${PROJECT_ROOT}/PHASE_COMPLETION_PROGRESS.md" ]; then
    echo "📊 Progress tracker: PHASE_COMPLETION_PROGRESS.md"
fi

echo ""

exit $EXIT_CODE
