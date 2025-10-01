# Makefile for NBA Simulator AWS Project
# Purpose: Automate common tasks, track file metadata, verify project state

.PHONY: help
help:
	@echo "NBA Simulator AWS - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "File Management:"
	@echo "  make inventory         Generate FILE_INVENTORY.md with all file summaries"
	@echo "  make describe FILE=... Show detailed info about a specific file"
	@echo "  make verify-files      Check all expected files exist"
	@echo ""
	@echo "Environment:"
	@echo "  make verify-env        Verify conda environment and dependencies"
	@echo "  make verify-aws        Verify AWS credentials and access"
	@echo "  make verify-all        Run all verification checks"
	@echo ""
	@echo "Documentation:"
	@echo "  make update-docs       Run documentation maintenance scripts"
	@echo "  make sync-progress     Check AWS resources vs PROGRESS.md"
	@echo "  make check-costs       Show current AWS costs"
	@echo ""
	@echo "Testing (future):"
	@echo "  make test              Run all tests"
	@echo "  make test-phase-2      Test Phase 2 components (Glue)"
	@echo "  make test-phase-3      Test Phase 3 components (RDS)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             Remove temporary files"
	@echo "  make backup            Create backup of critical files"
	@echo "  make stats             Show project statistics"

# ============================================================================
# File Management
# ============================================================================

.PHONY: inventory
inventory:
	@echo "🔍 Generating FILE_INVENTORY.md..."
	@python scripts/maintenance/generate_inventory.py
	@echo "✅ FILE_INVENTORY.md updated"

.PHONY: describe
describe:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make describe FILE=path/to/file"; \
		exit 1; \
	fi
	@python scripts/maintenance/describe_file.py "$(FILE)"

.PHONY: verify-files
verify-files:
	@echo "🔍 Verifying expected files exist..."
	@python scripts/maintenance/verify_files.py

# ============================================================================
# Environment Verification
# ============================================================================

.PHONY: verify-env
verify-env:
	@echo "🔍 Verifying conda environment..."
	@./scripts/shell/verify_setup.sh

.PHONY: verify-aws
verify-aws:
	@echo "🔍 Verifying AWS credentials..."
	@aws sts get-caller-identity > /dev/null 2>&1 && echo "✅ AWS credentials valid" || (echo "❌ AWS credentials invalid" && exit 1)
	@aws s3 ls s3://nba-sim-raw-data-lake/ > /dev/null 2>&1 && echo "✅ S3 bucket accessible" || (echo "❌ S3 bucket not accessible" && exit 1)

.PHONY: verify-all
verify-all: verify-env verify-aws verify-files
	@echo ""
	@echo "✅ All verifications passed!"

# ============================================================================
# Documentation
# ============================================================================

.PHONY: update-docs
update-docs:
	@echo "📝 Running documentation maintenance..."
	@./scripts/maintenance/update_docs.sh

.PHONY: sync-progress
sync-progress:
	@echo "🔄 Checking AWS resources vs PROGRESS.md..."
	@python scripts/maintenance/sync_progress.py

.PHONY: check-costs
check-costs:
	@echo "💰 Checking AWS costs..."
	@./scripts/aws/check_costs.sh

# ============================================================================
# Testing (placeholders for future phases)
# ============================================================================

.PHONY: test
test:
	@echo "🧪 Running tests..."
	@if [ -d "tests" ]; then \
		pytest tests/ -v; \
	else \
		echo "⚠️  Tests directory not created yet"; \
	fi

.PHONY: test-phase-2
test-phase-2:
	@echo "🧪 Testing Phase 2 (Glue) components..."
	@echo "⏸️  Phase 2 not yet implemented"

.PHONY: test-phase-3
test-phase-3:
	@echo "🧪 Testing Phase 3 (RDS) components..."
	@echo "⏸️  Phase 3 not yet implemented"

# ============================================================================
# Utilities
# ============================================================================

.PHONY: clean
clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@rm -f sample*.json 2>/dev/null || true
	@echo "✅ Cleanup complete"

.PHONY: backup
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='data' \
		--exclude='backups' \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='.idea' \
		PROGRESS.md CLAUDE.md QUICKSTART.md COMMAND_LOG.md \
		docs/ scripts/ sql/ .env.example Makefile
	@echo "✅ Backup created in backups/"

.PHONY: stats
stats:
	@echo "📊 Project Statistics"
	@echo "===================="
	@echo "Git commits:        $$(git rev-list --count HEAD 2>/dev/null || echo '0')"
	@echo "Documentation files: $$(find docs -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
	@echo "Python files:       $$(find . -name '*.py' | grep -v __pycache__ | wc -l | tr -d ' ')"
	@echo "Shell scripts:      $$(find scripts -name '*.sh' 2>/dev/null | wc -l | tr -d ' ')"
	@echo "SQL files:          $$(find sql -name '*.sql' 2>/dev/null | wc -l | tr -d ' ')"
	@echo "ADRs:               $$(find docs/adr -name '[0-9]*.md' 2>/dev/null | wc -l | tr -d ' ')"
	@echo ""
	@echo "Lines of code:"
	@echo "  Python:           $$(find . -name '*.py' | grep -v __pycache__ | xargs wc -l 2>/dev/null | tail -1 | awk '{print $$1}' || echo '0')"
	@echo "  Shell:            $$(find scripts -name '*.sh' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $$1}' || echo '0')"
	@echo "  SQL:              $$(find sql -name '*.sql' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $$1}' || echo '0')"
	@echo "  Documentation:    $$(find docs -name '*.md' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $$1}' || echo '0')"

# ============================================================================
# Phase-Specific Tasks (future)
# ============================================================================

.PHONY: setup-glue
setup-glue:
	@echo "⚙️  Setting up AWS Glue Crawler..."
	@echo "⏸️  Not yet implemented - see PROGRESS.md Phase 2.1"

.PHONY: setup-rds
setup-rds:
	@echo "⚙️  Setting up RDS PostgreSQL..."
	@echo "⏸️  Not yet implemented - see PROGRESS.md Phase 3.1"

.PHONY: run-etl
run-etl:
	@echo "⚙️  Running Glue ETL job..."
	@echo "⏸️  Not yet implemented - see PROGRESS.md Phase 2.2"

# ============================================================================
# Development Helpers
# ============================================================================

.PHONY: activate
activate:
	@echo "To activate conda environment, run:"
	@echo "  conda activate nba-aws"

.PHONY: deactivate
deactivate:
	@echo "To deactivate conda environment, run:"
	@echo "  conda deactivate"

.PHONY: git-status
git-status:
	@git status --short
	@echo ""
	@echo "Recent commits:"
	@git log --oneline -5

# Default target
.DEFAULT_GOAL := help
