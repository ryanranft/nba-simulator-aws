#!/bin/bash
################################################################################
# Configure Scheduled Wake/Sleep for Overnight Workflow
#
# This script configures your Mac to:
# - Wake at 2:55 AM daily (5 min before workflow runs at 3:00 AM)
# - Allow the overnight workflow to execute
# - Return to sleep automatically after completion
#
# Usage:
#   sudo bash scripts/setup/configure_scheduled_wake.sh
#
# Version: 1.0
# Created: October 9, 2025
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================="
echo "  Scheduled Wake/Sleep Configuration"
echo "========================================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo privileges"
   echo "Usage: sudo bash $0"
   exit 1
fi

echo -e "${BLUE}Current power settings:${NC}"
pmset -g | grep -E "(powernap|sleep|disksleep)"
echo ""

echo -e "${BLUE}Current scheduled events:${NC}"
pmset -g sched
echo ""

# Configure scheduled wake
echo -e "${YELLOW}Configuring scheduled wake at 2:55 AM daily...${NC}"
pmset repeat wakeorpoweron MTWRFSU 02:55:00

echo -e "${GREEN}✓${NC} Scheduled wake configured"
echo ""

# Enable Power Nap (allows some tasks while sleeping)
echo -e "${YELLOW}Enabling Power Nap...${NC}"
pmset -a powernap 1

echo -e "${GREEN}✓${NC} Power Nap enabled"
echo ""

# Verify configuration
echo "========================================================================="
echo "  Configuration Complete"
echo "========================================================================="
echo ""

echo -e "${GREEN}Your Mac is now configured to:${NC}"
echo "  1. Wake automatically at 2:55 AM every day"
echo "  2. Run the overnight workflow at 3:00 AM (~6 min runtime)"
echo "  3. Return to sleep automatically after completion"
echo ""

echo -e "${BLUE}Scheduled events:${NC}"
pmset -g sched
echo ""

echo -e "${BLUE}Power settings:${NC}"
pmset -g | grep -E "(powernap|sleep)"
echo ""

echo "========================================================================="
echo "  What to do tonight"
echo "========================================================================="
echo ""
echo "1. Close your laptop lid (or let it sleep normally)"
echo "2. Mac will wake at 2:55 AM"
echo "3. Workflow runs at 3:00 AM"
echo "4. Mac returns to sleep automatically"
echo ""
echo "Tomorrow morning (after 3:30 AM), verify with:"
echo "  bash scripts/monitoring/check_overnight_status.sh"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""

# Optional: Show power consumption estimate
echo "========================================================================="
echo "  Power Usage Info"
echo "========================================================================="
echo ""
echo "Sleep mode power consumption: ~1-2 watts"
echo "Monthly cost estimate: ~\$0.20 (at \$0.12/kWh)"
echo "Annual cost estimate: ~\$2.40"
echo ""
echo "This is negligible compared to shutting down and restarting daily."
echo ""
