## 🔧 Makefile Workflow Quick Reference

**Common Makefile targets available in this project**

### Verification Commands

```bash
make verify-env         # Verify conda environment
make verify-aws         # Verify AWS credentials and connectivity
make verify-files       # Check expected files exist
make verify-all         # Run all verifications
```

### Documentation Commands

```bash
make inventory          # Update FILE_INVENTORY.md
make update-docs        # Weekly maintenance (inventory + checks)
make sync-progress      # Sync PROGRESS.md with actual AWS resources
make stats              # Show project statistics
make describe FILE=...  # Show detailed file info
```

### Cost Management Commands

```bash
make check-costs        # Check current AWS costs
```

### Backup Commands

```bash
make backup             # Create full backup of working tree
```

### Cleanup Commands

```bash
make clean              # Remove temporary files
```

### AWS Resource Setup Commands

```bash
make setup-glue         # Set up AWS Glue Crawler
make setup-rds          # Set up RDS PostgreSQL
make run-etl            # Execute Glue ETL job
```

**See `Makefile` for complete command list and implementation**

---

## 🎯 Summary - Priority Order

**Every session follows this order:**

1. ✅ Initialize session (`session_manager.sh start`)
2. ✅ Orient to current state (read PROGRESS.md)
3. ✅ Ask about completed work
4. ✅ Offer time-based maintenance (if applicable)
5. ✅ Wait for user's task request
6. ✅ Follow decision workflow (check plan, prerequisites, costs, risks)
7. ✅ Execute task (following specific workflow for task type)
8. ✅ Document outcome (COMMAND_LOG.md, inventories, updates)
9. ✅ Wait for confirmation before marking complete
10. ✅ Update PROGRESS.md
11. ✅ Follow security protocol for commits (scan, approve, commit)
12. ✅ Follow pre-push protocol for pushes (inspect, approve, push)
13. ✅ Offer documentation updates (if triggered)
14. ✅ Suggest next action
15. ✅ Monitor context usage (auto-save at 75%, warn at 90%)
16. ✅ Session end reminders

