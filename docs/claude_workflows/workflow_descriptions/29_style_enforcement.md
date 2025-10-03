# Workflow #29: Style Guide Enforcement

**Category:** Code Quality
**Priority:** Medium
**When to Use:** When writing code or when patterns emerge 3+ times
**Related Workflows:** #5 (Task Execution), #6 (File Creation)

---

## Overview

This workflow ensures consistent code style across the project. It defines when to enforce existing style rules and when to add new rules to the style guide.

**Philosophy:** Consistency > personal preference. Follow the guide even if you disagree.

---

## When to Use This Workflow

### Apply Style Rules When:
- Writing any new code
- Refactoring existing code
- Reviewing code before commit
- Creating new files

### Update Style Guide When:
- Pattern used 3+ times (establishes precedent)
- Readability improvement discovered
- Team convention emerging
- Language-specific best practice identified

---

## Part 1: Enforcing Existing Style Rules

### Step 1: Read Current Style Guide

```bash
# Review style guide before writing code
cat docs/STYLE_GUIDE.md
```

**Key sections:**
- Naming conventions (snake_case, PascalCase, UPPER_CASE)
- Python style (PEP 8, line length, imports)
- SQL style (uppercase keywords, explicit JOINs)
- Docstring requirements
- Type hints policy

---

### Step 2: Apply Naming Conventions

#### Files and Modules
```bash
# Good
glue_etl_job.py
sanitize_command_log.sh
field_mapping.yaml

# Bad
GlueETLJob.py
Sanitize-Command-Log.sh
FieldMapping.yaml
```

#### Variables and Functions
```python
# Good - snake_case
player_stats = get_player_data(game_id)
total_points = calculate_points(player_stats)

# Bad - camelCase
playerStats = getPlayerData(gameId)
```

#### Classes
```python
# Good - PascalCase
class GameSimulator:
    pass

class PlayerStatistics:
    pass

# Bad - snake_case
class game_simulator:
    pass
```

#### Constants
```python
# Good - UPPER_SNAKE_CASE
MAX_RETRIES = 3
S3_BUCKET_NAME = "nba-sim-raw-data-lake"

# Bad - lowercase
max_retries = 3
```

---

### Step 3: Format Code According to Style

#### Python Formatting

```python
# Good - proper spacing, line length, imports
import os
import sys
from typing import Dict, List, Optional

import boto3
import pandas as pd

from scripts.utils.logger import setup_logger


def extract_player_stats(
    raw_data: Dict,
    season: str = "2023-24"
) -> Dict[str, int]:
    """Extract player statistics from raw JSON data.

    Args:
        raw_data: Dictionary containing player data from API
        season: NBA season (e.g., "2023-24")

    Returns:
        Dictionary with player_id and statistics

    Raises:
        KeyError: If required fields are missing
    """
    player_id = raw_data["id"]
    stats = raw_data.get("statistics", {})

    return {
        "player_id": player_id,
        "points": stats.get("points", 0),
        "rebounds": stats.get("rebounds", 0),
        "assists": stats.get("assists", 0)
    }
```

**Key points:**
- Import order: stdlib → third-party → local
- Line length: 100 characters max
- Type hints on all functions
- Docstrings required (Google style)
- 4 spaces for indentation (never tabs)

#### SQL Formatting

```sql
-- Good - uppercase keywords, explicit JOINs
SELECT
    g.game_id,
    g.game_date,
    t1.team_name AS home_team,
    t2.team_name AS away_team,
    g.home_score,
    g.away_score
FROM games g
INNER JOIN teams t1 ON g.home_team_id = t1.team_id
INNER JOIN teams t2 ON g.away_team_id = t2.team_id
WHERE g.season = '2023-24'
    AND g.game_date >= '2024-01-01'
ORDER BY g.game_date DESC;

-- Bad - lowercase, implicit joins
select g.game_id, g.game_date, t1.team_name, g.home_score
from games g, teams t1
where g.home_team_id = t1.team_id
and g.season = '2023-24';
```

---

### Step 4: Add Required Documentation

#### Function Docstrings
```python
def calculate_player_efficiency(stats: Dict) -> float:
    """Calculate player efficiency rating (PER).

    Args:
        stats: Dictionary containing player statistics
               Required keys: points, rebounds, assists, steals, blocks,
                             turnovers, minutes_played

    Returns:
        Player efficiency rating as float (typically 0-40 range)

    Raises:
        ValueError: If minutes_played is 0 or negative
        KeyError: If required statistics are missing

    Examples:
        >>> stats = {"points": 25, "rebounds": 10, "assists": 8,
        ...          "steals": 2, "blocks": 1, "turnovers": 3,
        ...          "minutes_played": 35}
        >>> calculate_player_efficiency(stats)
        24.5

    Note:
        PER formula based on John Hollinger's efficiency metric.
        League average is normalized to 15.0.
    """
    # Implementation
```

**Required sections:**
- Summary (one line)
- Args (with types and description)
- Returns (with type and description)
- Raises (all exceptions)
- Examples (optional but recommended)

#### Module Docstrings
```python
"""Player statistics extraction and transformation.

This module handles extraction of player data from ESPN API JSON files
and transforms it into structured format for database storage.

Key functions:
    - extract_player_stats: Parse raw JSON into player statistics
    - validate_player_data: Ensure data quality and schema compliance
    - transform_for_db: Convert to database-ready format

Example usage:
    from scripts.etl.player_extraction import extract_player_stats

    with open('raw_data.json') as f:
        raw_data = json.load(f)

    stats = extract_player_stats(raw_data)
"""
```

---

### Step 5: Run Auto-Formatting Tools (Optional)

```bash
# Install formatters
pip install black isort pylint mypy

# Format code
black scripts/
isort scripts/

# Check style compliance
pylint scripts/etl/field_mapping.py

# Type checking
mypy scripts/etl/field_mapping.py
```

**Black configuration** (pyproject.toml):
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**isort configuration** (pyproject.toml):
```toml
[tool.isort]
profile = "black"
line_length = 100
```

---

## Part 2: Adding New Style Rules

### When to Add Style Rules

✅ **ADD when:**
- Pattern used 3+ times (establishes precedent)
- Readability improvement needed
- Team convention emerging
- Language-specific best practice

❌ **DON'T ADD when:**
- Personal preference without rationale
- One-off exception
- Already covered in official guides (PEP 8, etc.)

---

### Step 1: Identify Pattern

**Check if pattern is recurring:**
```bash
# Search codebase for pattern
grep -r "pattern" scripts/

# If pattern appears 3+ times, consider adding to style guide
```

**Example patterns:**
- Error handling approach
- Logging format
- Configuration loading
- Data validation
- Import organization

---

### Step 2: Document the Rule

```markdown
## [Section Name]

### [Rule Name]

**Rule:** [Clear statement of the rule]

**Rationale:** [Why this rule exists]

**Good:**
[code example]

**Bad:**
[anti-pattern example]
```

**Example:**
```markdown
### Error Handling

**Rule:** Always log errors with context before re-raising

**Rationale:** Helps debugging by preserving stack trace and adding context

**Good:**
```python
try:
    result = process_data(file_path)
except Exception as e:
    logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
    raise
```

**Bad:**
```python
try:
    result = process_data(file_path)
except Exception:
    pass  # Silently swallow error
```
```

---

### Step 3: Add to STYLE_GUIDE.md

```bash
# Edit style guide
nano docs/STYLE_GUIDE.md

# Add new rule in appropriate section
```

**Structure:**
1. Find relevant section (Python / SQL / Shell / etc.)
2. Add new subsection
3. Include good/bad examples
4. Explain rationale

---

### Step 4: Update Existing Code (Optional)

If new rule conflicts with existing code:

**Option 1: Update immediately**
```bash
# Fix all violations now
# Good if rule is critical or easy to fix
```

**Option 2: Update gradually**
```bash
# Fix violations as you touch files
# Good if rule is cosmetic or large refactor needed
```

**Document decision:**
```markdown
**Status:** Added 2025-10-02. Existing code will be updated gradually.
```

---

### Step 5: Commit Style Guide Update

```bash
git add docs/STYLE_GUIDE.md

git commit -m "Add style rule for [pattern name]

Added rule: [brief description]

Rationale: [why this improves code quality]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Common Style Patterns in This Project

### Pattern 1: Type Hints Everywhere

```python
# Always use type hints
def process_game(game_id: str, season: str) -> Dict[str, Any]:
    """Process game data."""
    pass

# Even for simple functions
def is_valid(value: int) -> bool:
    """Check if value is valid."""
    return value > 0
```

### Pattern 2: Explicit is Better Than Implicit

```python
# Good - explicit dict access with .get()
points = stats.get("points", 0)

# Bad - implicit KeyError risk
points = stats["points"]
```

### Pattern 3: Guard Clauses

```python
# Good - early returns
def process_player(player_data: Dict) -> Optional[Dict]:
    if not player_data:
        return None

    if "id" not in player_data:
        logger.warning("Player missing ID")
        return None

    # Main logic here
    return processed_data

# Bad - nested ifs
def process_player(player_data: Dict) -> Optional[Dict]:
    if player_data:
        if "id" in player_data:
            # Main logic deeply nested
            return processed_data
```

### Pattern 4: Descriptive Variable Names

```python
# Good - clear intent
player_game_statistics = extract_statistics(raw_json)
home_team_total_points = calculate_team_score(home_players)

# Bad - unclear abbreviations
pgs = extract_statistics(raw_json)
htp = calculate_team_score(hp)
```

---

## Style Enforcement Checklist

**Before committing code:**
- [ ] Naming conventions followed (snake_case, PascalCase, UPPER_CASE)
- [ ] Type hints added to all functions
- [ ] Docstrings added (Google style)
- [ ] Imports organized (stdlib → third-party → local)
- [ ] Line length < 100 characters
- [ ] No tabs (4 spaces only)
- [ ] SQL keywords uppercase
- [ ] Ran auto-formatter (black, isort) if available

**Before adding new style rule:**
- [ ] Pattern appears 3+ times in codebase
- [ ] Rule has clear rationale (not just preference)
- [ ] Good and bad examples documented
- [ ] Rule doesn't conflict with existing guide

---

## Auto-Formatting Tools Configuration

### pyproject.toml
```toml
[tool.black]
line-length = 100
target-version = ['py311']
extend-exclude = '''
/(
  | venv
  | .venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip = [".venv", "venv", "build", "dist"]

[tool.pylint]
max-line-length = 100
disable = [
    "C0111",  # missing-docstring (we enforce via other means)
]
```

### .editorconfig
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.sh]
indent_style = space
indent_size = 2
```

---

## Integration with Other Workflows

**When writing code:**
1. Follow this style workflow (#29)
2. Write tests (TDD workflow #27)
3. Log code snippet (workflow #30)
4. Create file (workflow #6)

**When pattern emerges:**
1. Add to STYLE_GUIDE.md (this workflow)
2. Update FILE_INVENTORY.md (workflow #13)
3. Commit changes (workflow #8)

---

## Troubleshooting

### Black and isort Conflict
```bash
# Use isort's black profile
# In pyproject.toml:
[tool.isort]
profile = "black"
```

### Pre-commit Hook for Auto-Formatting
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
EOF

# Install hooks
pre-commit install
```

---

## Resources

**Style References:**
- `docs/STYLE_GUIDE.md` - Project style guide
- [PEP 8](https://peps.python.org/pep-0008/) - Python style guide
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Documentation](https://black.readthedocs.io/)

**Tools:**
```bash
pip install black isort pylint mypy
pip install pre-commit  # Optional: auto-format on commit
```

---

**Last Updated:** 2025-10-02
**Source:** docs/STYLE_GUIDE.md, docs/SESSION_INITIALIZATION.md (lines 157-171)
