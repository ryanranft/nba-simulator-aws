# Contributing to NBA Temporal Panel Data System

Thank you for your interest in contributing to this project! This guide will help you get started.

---

## Phase Naming Convention (ADR-010)

We use **4-digit zero-padded sub-phase numbering** for all phase organization.

### Format

**Standard format:** `N.MMMM_name`

- **N:** Phase number (0-9)
- **MMMM:** Sub-phase number (0001-9999, zero-padded to 4 digits)
- **name:** Descriptive snake_case name

### Examples

✅ **Correct:**
- `0.0001_basketball_reference`
- `0.0010_postgresql_jsonb_storage`
- `5.0121_implement_ab_testing`

❌ **Incorrect (old format):**
- `0.0001_basketball_reference` ← Will fail pre-commit hook
- `0.0010_postgresql_jsonb_storage` ← Creates sorting ambiguity
- `5.0121_implement_ab_testing` ← Not zero-padded

### Rationale

See [ADR-010](docs/adr/010-four-digit-subphase-numbering.md) for complete decision context:

- **Eliminates sorting ambiguity:** `0.0001`, `0.0002`, ..., `0.0010`, `0.0011` sorts correctly
- **Future-proof:** Supports up to 9,999 sub-phases per phase
- **Visual clarity:** Zero-padding creates alignment in directory listings
- **Automated validation:** Pre-commit hooks prevent old format usage

---

## Creating New Sub-Phases

### Step 1: Find Next Available Number

Check the phase index file to find the next available sub-phase number:

```bash
# For Phase 0
cat docs/phases/PHASE_0_INDEX.md

# For Phase 5
cat docs/phases/PHASE_5_INDEX.md
```

Look for the highest existing number and add 1.

### Step 2: Create Directory Structure

**For simple sub-phases:** Create a single markdown file

```bash
# Example: Phase 0, Sub-phase 23
touch docs/phases/phase_0/0.0023_my_new_feature.md
```

**For complex sub-phases:** Use power directory structure

```bash
# Create directory with README
mkdir -p docs/phases/phase_0/0.0023_my_new_feature
touch docs/phases/phase_0/0.0023_my_new_feature/README.md
touch docs/phases/phase_0/0.0023_my_new_feature/implement_my_feature.py
touch docs/phases/phase_0/0.0023_my_new_feature/test_my_feature.py
```

### Step 3: Update Phase Index

Add your new sub-phase to the appropriate `PHASE_N_INDEX.md` file:

```markdown
| 0.0023 | My New Feature | ⏸️ PENDING | Brief description... |
```

### Step 4: Create Tests/Validators (if applicable)

```bash
# Tests
touch tests/phases/phase_0/test_0_0023_my_new_feature.py

# Validators
touch validators/phases/phase_0/validate_0_0023_my_new_feature.py
```

### Step 5: Validate Format

Before committing, run validation:

```bash
# Validate phase numbering format
bash scripts/maintenance/validate_phase_numbering.sh

# Should output: ✅ ALL CHECKS PASSING
```

---

## Running Validation

### Pre-Commit Validation (Automatic)

The pre-commit hook automatically validates phase numbering format:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Test manually
pre-commit run validate-phase-numbering --all-files
```

### Manual Validation

```bash
# Validate all phase numbering
bash scripts/maintenance/validate_phase_numbering.sh

# Validate specific phase
python scripts/automation/validate_phase.py 0
```

---

## Code Style

### Python

- **Style:** PEP 8 compliant
- **Formatter:** Black (line length 88)
- **Type hints:** Required for all functions
- **Docstrings:** Google style

```python
def calculate_points_per_possession(
    team_id: str,
    game_id: str,
    timestamp: datetime
) -> float:
    """Calculate team's points per possession at exact timestamp.

    Args:
        team_id: NBA team identifier (e.g., 'LAL')
        game_id: Unique game identifier
        timestamp: Exact moment in time for query

    Returns:
        Points per possession as float

    Raises:
        ValueError: If team_id or game_id invalid
    """
    pass
```

### Bash Scripts

- **Shellcheck:** All scripts must pass shellcheck
- **Error handling:** Always use `set -e` and `set -u`
- **Functions:** Use functions for reusable code
- **Comments:** Explain non-obvious logic

```bash
#!/bin/bash
set -e  # Exit on error
set -u  # Exit on undefined variable

# Brief description of what script does
# Usage: ./script.sh <arg1> <arg2>
```

### Markdown

- **Linting:** Follows markdownlint rules
- **Headings:** Use ATX-style (`## Heading`)
- **Lists:** Consistent indentation (2 spaces)
- **Code blocks:** Always specify language

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/phases/phase_0/ -v

# Run with coverage
pytest --cov=scripts --cov-report=html
```

### Writing Tests

- **Location:** `tests/phases/phase_N/test_N_MMMM_name.py`
- **Naming:** Functions start with `test_`
- **Coverage:** Aim for 80%+ coverage
- **Fixtures:** Use pytest fixtures for common setup

```python
import pytest
from scripts.my_module import my_function

def test_my_function_basic():
    """Test basic functionality of my_function."""
    result = my_function(input_data)
    assert result == expected_output

def test_my_function_error_handling():
    """Test error handling in my_function."""
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

---

## Git Workflow

### Branch Strategy

- **Main branch:** `main` (protected, requires PR review)
- **Feature branches:** `feature/description` or `phase-N-MMMM-feature-name`
- **Bug fixes:** `fix/description`
- **Documentation:** `docs/description`

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(phase-0): Add basketball-reference scraper

Implements comprehensive scraper for basketball-reference.com
with retry logic and rate limiting.

refactor: Migrate Phase 0 to 4-digit sub-phase format (ADR-010)

docs: Update CONTRIBUTING.md with phase naming convention
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

3. **Push to remote**
   ```bash
   git push origin feature/my-new-feature
   ```

4. **Create PR on GitHub**
   - Provide clear description
   - Link related issues
   - Request review

5. **Address review feedback**
   - Make requested changes
   - Push updates to same branch
   - PR updates automatically

6. **Merge after approval**
   - Squash and merge (preferred)
   - Delete feature branch after merge

---

## Security

### Pre-Commit Hooks

The project uses pre-commit hooks to scan for security issues:

- **detect-secrets:** Scans for AWS keys, tokens, passwords
- **bandit:** Python security linting
- **black:** Code formatting
- **validate-phase-numbering:** ADR-010 compliance

### Never Commit

❌ **Do not commit:**
- `.env` files
- AWS credentials
- Private keys
- Passwords or tokens
- Large data files (>100 MB)
- Personal identifying information

✅ **Safe to commit:**
- Configuration templates
- Documentation
- Code and tests
- Example data (<1 MB)

### Running Security Scans

```bash
# Pre-push security scan
bash scripts/shell/pre_push_inspector.sh full

# Scan for secrets
detect-secrets scan --all-files

# Python security scan
bandit -r scripts/ -ll
```

---

## Documentation

### Where to Document

- **ADRs (Architectural Decision Records):** `docs/adr/` - For significant decisions
- **Phase documentation:** `docs/phases/phase_N/` - Implementation details
- **Workflows:** `docs/claude_workflows/` - Process documentation
- **README.md:** High-level project overview
- **CLAUDE.md:** AI assistant instructions
- **PROGRESS.md:** Implementation roadmap

### Writing Documentation

- **Clarity:** Write for someone unfamiliar with the project
- **Examples:** Include code examples and command snippets
- **Links:** Cross-reference related documentation
- **Maintenance:** Update docs when changing functionality

---

## Getting Help

### Resources

- **Documentation:** `docs/README.md` - Complete documentation index
- **Quick start:** `QUICKSTART.md` - Common commands
- **Troubleshooting:** `docs/TROUBLESHOOTING.md` - Common issues and solutions
- **ADR-010:** `docs/adr/010-four-digit-subphase-numbering.md` - Phase naming details

### Asking Questions

1. **Check existing documentation** - Search docs/ directory
2. **Review ADRs** - Check if decision already documented
3. **Search issues** - Someone may have asked already
4. **Create issue** - Provide context and examples

---

## License

This project is licensed under [MIT License](LICENSE).

---

## Questions?

If you have questions about contributing, please open an issue on GitHub with the `question` label.

---

**Thank you for contributing!** 🎉
