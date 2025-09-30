#!/bin/bash

# log_command.sh
# Automatically execute and log terminal commands to COMMAND_LOG.md
#
# Usage:
#   source scripts/shell/log_command.sh
#   log_cmd git status
#   log_cmd aws s3 ls s3://nba-sim-raw-data-lake/

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_FILE="$PROJECT_ROOT/COMMAND_LOG.md"

# Function to determine command category
get_category() {
    local cmd="$1"
    case "$cmd" in
        git*) echo "GIT" ;;
        aws*) echo "AWS" ;;
        conda*|pip*) echo "CONDA" ;;
        python*|python3*) echo "PYTHON" ;;
        psql*|mysql*) echo "DATABASE" ;;
        docker*) echo "DOCKER" ;;
        npm*|yarn*|node*) echo "NODE" ;;
        *) echo "OTHER" ;;
    esac
}

# Function to get brief description based on command
get_description() {
    local cmd="$1"
    case "$cmd" in
        git\ status) echo "Check Git status" ;;
        git\ push*) echo "Push commits to remote" ;;
        git\ pull*) echo "Pull changes from remote" ;;
        git\ commit*) echo "Create commit" ;;
        git\ add*) echo "Stage files" ;;
        aws\ s3\ ls*) echo "List S3 objects" ;;
        aws\ s3\ cp*) echo "Copy S3 objects" ;;
        aws\ glue*) echo "AWS Glue operation" ;;
        conda\ activate*) echo "Activate conda environment" ;;
        *) echo "Execute command" ;;
    esac
}

# Main logging function
log_cmd() {
    # Check if any arguments provided
    if [ $# -eq 0 ]; then
        echo "❌ Usage: log_cmd <command> [args...]"
        echo "Example: log_cmd git status"
        return 1
    fi

    # Capture command arguments
    local cmd="$*"
    local category=$(get_category "$cmd")
    local description=$(get_description "$cmd")
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local current_dir=$(pwd)
    local conda_env="${CONDA_DEFAULT_ENV:-N/A}"

    # Create temporary file for output
    local temp_output=$(mktemp)

    echo ""
    echo "📝 Logging command: $cmd"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Execute command and capture output and exit code
    eval "$cmd" 2>&1 | tee "$temp_output"
    local exit_code=${PIPESTATUS[0]}

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Determine result status
    local result
    local result_emoji
    if [ $exit_code -eq 0 ]; then
        # Check if stderr had warnings (output contains "warning" case-insensitive)
        if grep -iq "warning" "$temp_output"; then
            result="⚠️ WARNING"
            result_emoji="⚠️"
            echo "⚠️  Command completed with warnings (exit code: 0)"
        else
            result="✅ SUCCESS"
            result_emoji="✅"
            echo "✅ Command completed successfully (exit code: 0)"
        fi
    else
        result="❌ ERROR"
        result_emoji="❌"
        echo "❌ Command failed (exit code: $exit_code)"
    fi

    # Read captured output
    local output=$(<"$temp_output")

    # Append to log file
    {
        echo ""
        echo "---"
        echo ""
        echo "### [$category] $description"
        echo "**Time:** $timestamp"
        echo "**Directory:** \`$current_dir\`"
        echo "**Conda Env:** $conda_env"
        echo "**Command:** \`$cmd\`"
        echo "**Output:**"
        echo '```'
        echo "$output"
        echo '```'
        echo "**Result:** $result"
        echo "**Exit Code:** $exit_code"
        if [ $exit_code -ne 0 ]; then
            echo "**Notes:** Command failed - add solution after resolving"
            echo "**Solution:** (To be added)"
        else
            echo "**Notes:** (Add any observations)"
        fi
        echo "**Related:** (Link to PROGRESS.md section if applicable)"
    } >> "$LOG_FILE"

    # Clean up
    rm -f "$temp_output"

    echo ""
    echo "📋 Logged to: $LOG_FILE"
    echo "🔗 View log: cat $LOG_FILE | tail -30"
    echo ""

    # Return the original exit code
    return $exit_code
}

# Helper function to add notes to the last logged command
log_note() {
    if [ $# -eq 0 ]; then
        echo "❌ Usage: log_note <your note text>"
        echo "Example: log_note This fixed the authentication issue"
        return 1
    fi

    local note="$*"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    # Find the last "**Notes:**" line and replace it
    # This is a simple implementation - could be improved
    echo ""
    echo "📌 Adding note to last command..."
    echo "Note: $note"
    echo ""

    # For now, just append to file (user can manually edit)
    echo "" >> "$LOG_FILE"
    echo "**Additional Note [$timestamp]:** $note" >> "$LOG_FILE"
}

# Helper function to add solution to the last logged command
log_solution() {
    if [ $# -eq 0 ]; then
        echo "❌ Usage: log_solution <solution description>"
        echo "Example: log_solution Used git pull --rebase to sync with remote"
        return 1
    fi

    local solution="$*"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    echo ""
    echo "💡 Adding solution to last command..."
    echo "Solution: $solution"
    echo ""

    echo "" >> "$LOG_FILE"
    echo "**Solution Added [$timestamp]:** $solution" >> "$LOG_FILE"
}

# Display helpful message when sourced
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Command logging functions loaded!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Available commands:"
echo "  log_cmd <command>       - Execute and log a command"
echo "  log_note <text>         - Add a note to the last logged command"
echo "  log_solution <text>     - Add a solution to the last logged command"
echo ""
echo "📋 Examples:"
echo "  log_cmd git status"
echo "  log_cmd aws s3 ls s3://nba-sim-raw-data-lake/"
echo "  log_note This command shows the current branch"
echo "  log_solution Used git remote set-url to fix the issue"
echo ""
echo "📂 Log file: $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"