# CLAUDE WORKFLOW ORDER

**This file defines the execution order for Claude Code workflows.**

All detailed workflow descriptions are located in: `/docs/claude_workflows/workflow_descriptions/`

## 🎯 Priority Order - Follow This Sequence

### Every Session (Mandatory)

1. **Session Start** → `01_session_start.md`
2. **🌙 Overnight Scraper Check** → `38_overnight_scraper_handoff.md` (if overnight jobs running - check PROGRESS.md)
   - **Use:** `bash scripts/monitoring/monitor_scrapers.sh` → See `39_scraper_monitoring_automation.md`
3. **Command Logging** → `02_command_logging.md` (automatic throughout session)

### When User Requests Task (Decision Point)

3. **Decision Workflow** → `03_decision_workflow.md`
4. **Plan Change Protocol** → `04_plan_change_protocol.md` (if needed)

### During Task Execution

5. **Task Execution** → `05_task_execution.md`
6. **File Creation/Modification** → `06_file_creation.md` (if creating/editing files)
7. **Repository Status Check** → `07_repo_status_check.md` (after file changes)

### After Completing Work (Git Operations)

8. **Git Commit** → `08_git_commit.md`
9. **Archive Management** → `09_archive_management.md` (recommended after commit)
10. **Git Push** → `10_git_push.md` (requires user approval)

### Error Handling (As Needed)

11. **Error Handling** → `11_error_handling.md`
12. **Troubleshooting Protocol** → `22_troubleshooting_protocol.md`

### Documentation Updates (Triggered)

13. **Documentation Triggers** → `12_documentation_triggers.md`

### Maintenance & Monitoring (Periodic)

14. **File Inventory** → `13_file_inventory.md` (automatic after file changes)
15. **Session End** → `14_session_end.md` (end of session)
16. **Context Management** → `15_context_management.md` (at 75%/90% context)

### Testing (By Phase)

17. **Testing Workflows** → `16_testing.md`

### Environment & Setup (Initial/Verification)

18. **Environment Setup** → `17_environment_setup.md`

### Cost & Budget (Before Creating Resources)

19. **Cost Management** → `18_cost_management.md`

### Backup & Safety (Before Destructive Operations)

20. **Backup & Recovery** → `19_backup_recovery.md`

### Scheduled Maintenance

21. **Maintenance Schedule** → `20_maintenance_schedule.md`
   - Weekly: Every Monday or 7+ days
   - Monthly: First Monday of month

### Data Operations (Before ETL/Simulation/ML)

22. **Data Validation** → `21_data_validation.md`

### Security Operations (Scheduled/Emergency)

23. **Credential Rotation** → `23_credential_rotation.md`

### AWS Resource Management (By Phase)

24. **AWS Resource Setup** → `24_aws_resource_setup.md`

### Database Operations (Phase 3)

25. **Database Migration** → `25_database_migration.md`

### Quick Reference

26. **Makefile Reference** → `26_makefile_reference.md`

### Code Quality & Development Practices

27. **TDD Workflow** → `27_tdd_workflow.md` (when writing new code)
28. **ADR Creation** → `28_adr_creation.md` (after architectural decisions)
29. **Style Enforcement** → `29_style_enforcement.md` (when writing/reviewing code)
30. **Code Snippet Logging** → `30_code_snippet_logging.md` (every code change)
31. **QUICKSTART Update** → `31_quickstart_update.md` (when daily workflows change)

### Testing & Deployment (Pre-Production)

35. **Pre-Deployment Testing** → `35_pre_deployment_testing.md` (before deploying AWS resources)
36. **Pre-Push Repository Cleanup** → `36_pre_push_repo_cleanup.md` (before pushing to GitHub)

### AWS Operations & Troubleshooting

32. **RDS Connection** → `32_rds_connection.md` (when connecting to PostgreSQL)
33. **Multi-Sport Reproduction** → `33_multi_sport_reproduction.md` (when adapting for new sport)
34. **Lessons Learned Review** → `34_lessons_learned_review.md` (before similar tasks to avoid known pitfalls)

---

## 📋 How to Use This System

### For Claude Code

1. **Start every session** by reading `01_session_start.md`
2. **When user requests work**, check `03_decision_workflow.md`
3. **Read only the relevant workflow file** for the current task
4. **Follow the numbered steps** in each workflow
5. **Never skip workflows** - they contain critical safety checks

### Navigation Pattern

```
PROGRESS.md (current task)
    ↓
CLAUDE_WORKFLOW_ORDER.md (find which workflow)
    ↓
workflow_descriptions/XX_workflow_name.md (detailed steps)
    ↓
Execute workflow steps
```

### Integration with PROGRESS.md

**Current behavior:**
- PROGRESS.md contains high-level phase descriptions
- Each phase references which workflow(s) to use

**Future enhancement (planned):**
- PROGRESS.md will become a directory system
- Each phase will have detailed plan file (e.g., `PHASE_2.2_ETL.md`)
- Phase files will contain thousands of in-depth instructions
- Phase files will reference specific workflows by number

**Example future structure:**
```
PROGRESS.md (directory/index)
  ↓
phases/PHASE_2.2_ETL.md (detailed plan)
  ↓
"Follow workflow #24 (AWS Resource Setup) for Glue job creation"
  ↓
claude_workflows/workflow_descriptions/24_aws_resource_setup.md
```

### Benefits of This System

✅ **Efficiency**: Load only what you need (not 9,533 lines)
✅ **Speed**: Faster file reads and edits
✅ **Organization**: Clear separation of concerns
✅ **Scalability**: Easy to add new workflows
✅ **Maintenance**: Update one workflow without affecting others
✅ **Context savings**: Reduce token usage by 90%+

---

## 🔍 Quick Workflow Finder

**Need to...**
- Start session? → `01`
- Make a decision? → `03`
- Create files? → `06`
- Commit code? → `08`
- Push to GitHub? → `10`
- Handle errors? → `11` or `22`
- End session? → `14`
- Save context? → `15`
- Run tests? → `16`
- Check environment? → `17`
- Estimate costs? → `18`
- Backup files? → `19`
- Weekly maintenance? → `20`
- Validate data? → `21`
- Rotate credentials? → `23`
- Create AWS resources? → `24`
- Migrate database? → `25`
- Find make command? → `26`
- Write tests first (TDD)? → `27`
- Document architectural decision? → `28`
- Apply code style rules? → `29`
- Log code changes? → `30`
- Update daily commands? → `31`
- Connect to RDS database? → `32`
- Adapt for another sport? → `33`
- Avoid known pitfalls? → `34`
- Pre-deployment testing? → `35`
- Repository cleanup before push? → `36`
- Credential management? → `37`
- **🌙 Overnight scraper running?** → `38` (check at session start)
- **Build possession panel data?** → `39` (possession-level ML features)
- **Run test suites?** → `41` (validation framework)
- **Launch data scrapers?** → `42` (multi-source scraper execution)
- **Consolidate/move documentation files?** → `43` (prevent broken links)
- **Validate file references after moves?** → `44` (NEW - automatic reference path validation)

---

## 📊 Workflow Statistics

- **Total workflows**: 44
- **Total size**: ~830 KB
- **Average workflow**: ~19 KB
- **Largest workflow**: `24_aws_resource_setup.md` (92 KB)
- **Smallest workflow**: `04_plan_change_protocol.md` (595 bytes)

**Old system**: 1 file, 9,533 lines, 284 KB (unreadable by Claude)
**New system**: 44 files, average 265 lines per file (fully readable)

**Workflow additions:**
- **Batch 1 (27-31):** Code quality workflows
  - 🧪 TDD Workflow - Test-driven development practice
  - 📝 ADR Creation - Document architectural decisions
  - 🎨 Style Enforcement - Code quality and consistency
  - 📋 Code Snippet Logging - Track code changes and outcomes
  - ⚡ QUICKSTART Update - Maintain daily command reference

- **Batch 2 (32-34):** AWS operations & troubleshooting workflows
  - 🔗 RDS Connection - Database connection procedures
  - 🏀 Multi-Sport Reproduction - Adapt pipeline for new sports
  - 📚 Lessons Learned Review - Avoid repeating known mistakes

- **Batch 3 (35-36):** Testing & deployment workflows
  - 🧪 Pre-Deployment Testing - Phase-specific testing checklists
  - 🧹 Pre-Push Repository Cleanup - Automated cleanup before push

- **Batch 4 (37-38):** Credential & scraper management
  - 🔐 Credential Management - Add/update AWS credentials to .env
  - 🌙 Overnight Scraper Handoff - Track and validate overnight jobs

- **Batch 5 (39):** Data pipeline documentation
  - 📊 Possession Panel Data Pipelines - Complete possession-level panel creation system

- **Batch 6 (41):** Testing framework integration
  - 🧪 Testing Framework - Comprehensive test suite validation (3 test suites: monitoring, temporal queries, feature engineering)

- **Batch 7 (42):** Scraper management & execution
  - 🕷️ Scraper Management - Multi-source scraper execution and monitoring (5 scrapers: NBA API, hoopR, Basketball Reference, Kaggle, ESPN)

- **Batch 8 (43):** Documentation organization
  - 📚 Documentation Consolidation - Systematic process for consolidating, moving, and archiving documentation files while preventing broken links

- **Batch 9 (44):** Automatic reference validation
  - 🔍 Reference Path Validator - Automatically detects moved/renamed/deleted files and finds all references in codebase; validates file paths before GitHub push

---

*Last updated: 2025-10-08*