#!/bin/bash
# 0.0012: Load secrets and run RAG+LLM system
# This script loads secrets from the hierarchical structure and runs the 0.0012 CLI

set -e

# Load secrets using Python hierarchical loader
echo "🔐 Loading NBA Simulator AWS secrets..."
python3 /Users/ryanranft/load_env_hierarchical.py nba-simulator-aws NBA production --export /tmp/nba_sim_env.sh

# Source the exported environment
if [ -f /tmp/nba_sim_env.sh ]; then
    source /tmp/nba_sim_env.sh
    rm /tmp/nba_sim_env.sh
fi

# Map hierarchical secret to expected variable name
if [ -n "$OPENAI_API_KEY_NBA_SIMULATOR_AWS_WORKFLOW" ]; then
    export OPENAI_API_KEY="$OPENAI_API_KEY_NBA_SIMULATOR_AWS_WORKFLOW"
    echo "✅ OpenAI API key loaded (${#OPENAI_API_KEY} characters)"
else
    echo "❌ OPENAI_API_KEY_NBA_SIMULATOR_AWS_WORKFLOW not found"
    exit 1
fi

# Map RDS credentials to PostgreSQL environment variables (both formats)
if [ -n "$RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW" ]; then
    # Standard PostgreSQL env vars
    export POSTGRES_HOST="$RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW"
    export POSTGRES_DB="$RDS_DATABASE_NBA_SIMULATOR_AWS_WORKFLOW"
    export POSTGRES_USER="$RDS_USERNAME_NBA_SIMULATOR_AWS_WORKFLOW"
    export POSTGRES_PASSWORD="$RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW"
    export POSTGRES_PORT="5432"

    # RDS-specific env vars (for 0.0011 compatibility)
    export RDS_HOST="$RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW"
    export RDS_DATABASE="$RDS_DATABASE_NBA_SIMULATOR_AWS_WORKFLOW"
    export RDS_USER="$RDS_USERNAME_NBA_SIMULATOR_AWS_WORKFLOW"
    export RDS_PASSWORD="$RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW"
    export RDS_PORT="5432"

    echo "✅ PostgreSQL credentials loaded (POSTGRES_* and RDS_* vars)"
fi

echo ""
echo "🚀 Running 0.0012 RAG+LLM CLI with loaded secrets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the 0.0012 CLI with all arguments
cd /Users/ryanranft/nba-simulator-aws
python3 scripts/0_12/main.py "$@"
