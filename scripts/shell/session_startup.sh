#!/bin/bash
# Session startup - Full diagnostics with concise output

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║ SESSION STARTUP: $(date '+%Y-%m-%d %H:%M:%S')                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# HARDWARE
echo ""
echo "▶ HARDWARE"
system_profiler SPHardwareDataType | grep -E "Model Name|Model Identifier|Chip|Total Number of Cores|Memory" | sed 's/^[[:space:]]*/  /'

# SYSTEM
echo ""
echo "▶ SYSTEM"
sw_vers | sed 's/^/  /'
echo "  Homebrew: $(brew --version | head -1 | awk '{print $2}') @ $(which brew)"

# CONDA
echo ""
echo "▶ CONDA ENVIRONMENT"
echo "  Version: $(conda --version | awk '{print $2}')"
echo "  Base: $(conda info --base)"
conda env list | grep '*' | sed 's/^/  Active: /'

# PYTHON
echo ""
echo "▶ PYTHON"
echo "  Version: $(python --version 2>&1)"
echo "  Location: $(which python)"
echo "  Packages:"
pip show boto3 pandas numpy 2>/dev/null | grep -E "^(Name|Version|Location):" | awk '{
    if ($1 == "Name:") name=$2
    if ($1 == "Version:") version=$2
    if ($1 == "Location:") {print "    - " name " " version " @ " $2; name=""; version=""}
}'

# AWS CLI
echo ""
echo "▶ AWS CLI"
aws --version 2>&1 | sed 's/^/  /'
echo "  Location: $(which aws)"

# GIT
echo ""
echo "▶ GIT"
echo "  Version: $(git --version)"
echo "  Location: $(which git)"
echo ""
echo "  Status:"
git status --short | head -20 | sed 's/^/    /'
if [ $(git status --short | wc -l) -gt 20 ]; then
    echo "    ... ($(git status --short | wc -l) total files changed)"
fi
echo "  Branch: $(git branch --show-current)"
echo "  Recent commits:"
git log --oneline -3 | sed 's/^/    /'

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║ ✓ Diagnostics complete - ready to work                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""