## 📊 Context Management Workflow

**Monitor context usage throughout session:**

### At 75% Context (~150K tokens)
**AUTOMATIC - Don't ask:**
- Save conversation verbatim to CHAT_LOG.md
- Notify user: "Context at 75% (~150K tokens) - auto-saved conversation to CHAT_LOG.md"

### At 90% Context (~180K tokens)
**URGENT - Strongly recommend:**
"Context at 90% (~180K tokens) - strongly urge committing changes NOW before context limit (200K)"

### User Says "Save This Conversation"
**AUTOMATIC - Don't ask:**
- Write verbatim transcript to CHAT_LOG.md
- Include timestamp and session context

### Manual Save with Script (Alternative Method)

**When to use:** User wants to trigger conversation save via script

**Script:** `scripts/shell/save_conversation.sh`

**What it does:**
1. Displays save conversation prompt
2. Shows what will be saved (verbatim transcript format)
3. Asks for confirmation
4. Outputs instructions for Claude to save conversation

**Usage:**
```bash
bash scripts/shell/save_conversation.sh
```

**Script output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 SAVE CONVERSATION TO CHAT_LOG.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This will trigger Claude to write the conversation transcript.

Claude will write:
  - Full verbatim conversation (your messages + Claude's responses)
  - All code snippets and commands
  - Timestamp and session info

Destination: /Users/ryanranft/nba-simulator-aws/CHAT_LOG.md

Continue? [y/N] y

📝 Prompting Claude to save conversation...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 CLAUDE: Please write the full verbatim conversation to CHAT_LOG.md

   Include:
   - Every user message (exact text)
   - Every assistant response (complete text)
   - All code blocks, commands, and tool outputs
   - Timestamp header with session date/time

   Format:
   # Claude Code Conversation - [Date/Time]

   User: [exact message]

   Assistant: [complete response]

   [Continue for entire conversation...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Waiting for Claude to write CHAT_LOG.md...
```

**When Claude saves conversation:**

Claude will write to `CHAT_LOG.md` with format:
```markdown
# Claude Code Conversation - 2025-10-02 18:45:23

**Session Info:**
- Date: 2025-10-02
- Time: 18:45:23
- Working Directory: /Users/ryanranft/nba-simulator-aws
- Context: [current task/phase]

---

## Conversation

**User:** [First user message]

**Assistant:** [First assistant response with complete text, code blocks, etc.]

**User:** [Second user message]

**Assistant:** [Second assistant response...]

[Continue for entire conversation...]

---

**End of Conversation**
```

**After save completes:**
- Review CHAT_LOG.md for completeness
- Archive conversation: `bash scripts/maintenance/archive_manager.sh conversation`
- Commit if needed: `git add CHAT_LOG.md && git commit -m "Save conversation log"`

**Note:** The script itself doesn't write CHAT_LOG.md - it prompts Claude to do so. This is a workflow trigger, not an automated writer.

### Context Tracking Notes
- **Total context limit:** 200K tokens
- **75% threshold:** 150K tokens (auto-save trigger)
- **90% threshold:** 180K tokens (urgent warning)
- **CHAT_LOG.md location:** Project root
- **Archive location:** `~/sports-simulator-archives/nba/chat-logs/`

### Integration with Archive Management

**After saving conversation to CHAT_LOG.md:**

1. **Archive immediately** (creates 3 versions):
   ```bash
   bash scripts/maintenance/archive_manager.sh conversation
   ```

2. **This creates:**
   - **ORIGINAL:** `~/sports-simulator-archives/nba/conversations/CHAT_LOG_<timestamp>.md`
     - Full conversation with real paths/IPs
     - **NEVER commit to GitHub**
   - **SANITIZED:** `~/sports-simulator-archives/nba/conversations/CHAT_LOG_SANITIZED_<timestamp>.md`
     - Credentials removed, IPs masked
     - **Safe for private repos**
   - **SPOOFED:** `~/sports-simulator-archives/nba/conversations/CHAT_LOG_SPOOFED_<timestamp>.md`
     - Fake paths for demonstration
     - **Safe for public sharing**

3. **Clear CHAT_LOG.md** (optional, to start fresh):
   ```bash
   # After archiving, optionally clear for next session
   > CHAT_LOG.md  # Clear contents
   echo "# Chat Log" > CHAT_LOG.md  # Or add header
   ```

**See Archive Management Workflow for complete archiving procedures**

---

