#!/bin/bash
# Save current Claude Code conversation to CHAT_LOG.md
# This script prompts Claude to write the conversation transcript

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHAT_LOG="$PROJECT_DIR/CHAT_LOG.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 SAVE CONVERSATION TO CHAT_LOG.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will trigger Claude to write the conversation transcript."
echo ""
echo "Claude will write:"
echo "  - Full verbatim conversation (your messages + Claude's responses)"
echo "  - All code snippets and commands"
echo "  - Timestamp and session info"
echo ""
echo "Destination: $CHAT_LOG"
echo ""

read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "📝 Prompting Claude to save conversation..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "👉 CLAUDE: Please write the full verbatim conversation to CHAT_LOG.md"
echo ""
echo "   Include:"
echo "   - Every user message (exact text)"
echo "   - Every assistant response (complete text)"
echo "   - All code blocks, commands, and tool outputs"
echo "   - Timestamp header with session date/time"
echo ""
echo "   Format:"
echo "   # Claude Code Conversation - [Date/Time]"
echo "   "
echo "   User: [exact message]"
echo "   "
echo "   Assistant: [complete response]"
echo "   "
echo "   [Continue for entire conversation...]"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ Waiting for Claude to write CHAT_LOG.md..."
echo ""