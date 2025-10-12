#!/bin/bash

##############################################################################
# Alert Notification System
##############################################################################
#
# Purpose: Send alerts via macOS notifications and email for audit issues
# Output: Desktop notifications and/or emails
# Cost: $0 (local notifications, email if configured)
#
# Usage:
#   bash scripts/audit/send_alert.sh <level> <title> <message>
#
# Levels:
#   INFO      - Informational (no alert during quiet hours)
#   WARNING   - Warning (desktop notification)
#   ERROR     - Error (desktop + email if configured)
#   CRITICAL  - Critical (desktop + email + sound)
#
# Options:
#   --force       Send alert even during quiet hours
#   --no-sound    Suppress notification sound
#   --email-only  Skip desktop notification, email only
#
# Environment Variables (optional):
#   ALERT_EMAIL       Email address to send alerts to
#   ALERT_FROM        From address for emails (default: nba-audit@localhost)
#   QUIET_HOURS_START Start of quiet hours (default: 22, 10 PM)
#   QUIET_HOURS_END   End of quiet hours (default: 8, 8 AM)
#   DISABLE_ALERTS    Set to "true" to disable all alerts
#
##############################################################################

set -e  # Exit on error

# Configuration
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_FROM="${ALERT_FROM:-nba-audit@localhost}"
QUIET_HOURS_START="${QUIET_HOURS_START:-22}"
QUIET_HOURS_END="${QUIET_HOURS_END:-8}"
DISABLE_ALERTS="${DISABLE_ALERTS:-false}"

# Parse arguments
LEVEL=""
TITLE=""
MESSAGE=""
FORCE=false
NO_SOUND=false
EMAIL_ONLY=false

# Parse level, title, message
if [ $# -lt 3 ]; then
    echo "Usage: $0 <level> <title> <message> [--force] [--no-sound] [--email-only]"
    echo "Levels: INFO, WARNING, ERROR, CRITICAL"
    exit 1
fi

LEVEL="$1"
TITLE="$2"
MESSAGE="$3"
shift 3

# Parse options
while [ $# -gt 0 ]; do
    case "$1" in
        --force) FORCE=true ;;
        --no-sound) NO_SOUND=true ;;
        --email-only) EMAIL_ONLY=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

##############################################################################
# Check if Alerts are Disabled
##############################################################################

if [ "$DISABLE_ALERTS" = "true" ]; then
    echo "Alerts disabled via DISABLE_ALERTS=true"
    exit 0
fi

##############################################################################
# Check Quiet Hours
##############################################################################

check_quiet_hours() {
    local current_hour=$(date +%H | sed 's/^0//')

    # If force flag is set, bypass quiet hours
    if [ "$FORCE" = true ]; then
        return 1  # Not in quiet hours (proceed with alert)
    fi

    # INFO level alerts respect quiet hours
    if [ "$LEVEL" = "INFO" ]; then
        if [ $current_hour -ge $QUIET_HOURS_START ] || [ $current_hour -lt $QUIET_HOURS_END ]; then
            return 0  # In quiet hours (skip alert)
        fi
    fi

    return 1  # Not in quiet hours (proceed with alert)
}

if check_quiet_hours; then
    echo "Quiet hours active - skipping $LEVEL alert"
    exit 0
fi

##############################################################################
# Determine Alert Icon and Sound
##############################################################################

get_icon() {
    case "$LEVEL" in
        INFO)     echo "ℹ️" ;;
        WARNING)  echo "⚠️" ;;
        ERROR)    echo "❌" ;;
        CRITICAL) echo "🚨" ;;
        *)        echo "📊" ;;
    esac
}

get_sound() {
    if [ "$NO_SOUND" = true ]; then
        echo ""
        return
    fi

    case "$LEVEL" in
        INFO)     echo "" ;;
        WARNING)  echo "Ping" ;;
        ERROR)    echo "Basso" ;;
        CRITICAL) echo "Sosumi" ;;
        *)        echo "" ;;
    esac
}

ICON=$(get_icon)
SOUND=$(get_sound)

##############################################################################
# Send macOS Desktop Notification
##############################################################################

send_macos_notification() {
    local title="$1"
    local message="$2"
    local sound="$3"

    # Build osascript command
    local script="display notification \"$message\" with title \"$ICON $title\""

    if [ -n "$sound" ]; then
        script="$script sound name \"$sound\""
    fi

    # Send notification
    osascript -e "$script" 2>/dev/null || {
        echo "Warning: Failed to send macOS notification"
        return 1
    }

    echo "Desktop notification sent: $title"
    return 0
}

##############################################################################
# Send Email Alert
##############################################################################

send_email_alert() {
    local title="$1"
    local message="$2"
    local level="$3"

    # Skip if no email configured
    if [ -z "$ALERT_EMAIL" ]; then
        return 0
    fi

    # Check if mail command is available
    if ! command -v mail &>/dev/null; then
        echo "Warning: mail command not available - skipping email alert"
        return 1
    fi

    # Create email body
    local email_body=$(cat <<EOF
NBA Data Audit Alert

Level: $level
Time: $(date '+%Y-%m-%d %H:%M:%S')
Title: $title

Message:
$message

---
This is an automated alert from the NBA Data Audit System.
To disable email alerts, unset ALERT_EMAIL environment variable.
EOF
)

    # Send email
    echo "$email_body" | mail -s "[$level] $title" "$ALERT_EMAIL" 2>/dev/null || {
        echo "Warning: Failed to send email alert to $ALERT_EMAIL"
        return 1
    }

    echo "Email alert sent to: $ALERT_EMAIL"
    return 0
}

##############################################################################
# Main Alert Logic
##############################################################################

# Log alert
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ALERT: [$LEVEL] $TITLE"
echo "Message: $MESSAGE"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Send desktop notification (unless --email-only)
if [ "$EMAIL_ONLY" = false ]; then
    send_macos_notification "$TITLE" "$MESSAGE" "$SOUND"
fi

# Send email for ERROR and CRITICAL levels
if [ "$LEVEL" = "ERROR" ] || [ "$LEVEL" = "CRITICAL" ]; then
    send_email_alert "$TITLE" "$MESSAGE" "$LEVEL"
fi

exit 0
