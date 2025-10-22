# DIMS Quick Reference

**Data Inventory Management System v1.0.0**

---

## Most Common Commands

### Daily Use
```bash
# Quick verification (no updates)
python scripts/monitoring/dims_cli.py verify

# Verify and auto-update drifted metrics
python scripts/monitoring/dims_cli.py verify --update

# Regenerate all documentation
python scripts/monitoring/dims_cli.py generate
```

### Weekly Maintenance
```bash
# Full refresh workflow
python scripts/monitoring/dims_cli.py snapshot
python scripts/monitoring/dims_cli.py update
python scripts/monitoring/dims_cli.py generate
python scripts/monitoring/dims_cli.py cache cleanup
```

---

## All Commands

### System Information
```bash
dims_cli.py info                    # Show DIMS configuration and status
```

### Verification
```bash
dims_cli.py verify                                         # Verify all metrics
dims_cli.py verify --update                                # Verify + auto-update
dims_cli.py verify --category CATEGORY                     # Verify category
dims_cli.py verify --category CATEGORY --metric METRIC     # Verify single metric
```

### Update Metrics
```bash
dims_cli.py update                                         # Update all metrics
dims_cli.py update --category CATEGORY --metric METRIC     # Update single metric
```

### Generate Outputs
```bash
dims_cli.py generate                    # Generate all outputs
dims_cli.py generate --format markdown  # Markdown only
dims_cli.py generate --format json      # JSON only
```

### Cache Management
```bash
dims_cli.py cache info      # Show cache statistics
dims_cli.py cache clear     # Clear all cache
dims_cli.py cache cleanup   # Remove expired entries only
```

### History & Snapshots
```bash
dims_cli.py history METRIC_PATH --days 30    # View metric trend
dims_cli.py snapshot                          # Create daily snapshot
```

---

## Metric Categories

| Category | Metrics | Volatility |
|----------|---------|------------|
| **s3_storage** | total_objects, total_size_gb, hoopr_files | Volatile |
| **prediction_system** | total_lines, 7 script line counts | Stable |
| **plus_minus_system** | total_lines, python_lines, sql_lines, docs_lines | Stable |
| **code_base** | python_files, ml_scripts, phase_9_scripts, test_files | Volatile |
| **documentation** | markdown_files, total_size_mb | Volatile |
| **git** | book_recommendation_commits | Stable |
| **workflows** | total | Stable |
| **sql_schemas** | total_lines | Stable |
| **local_data** | espn_size_gb (disabled by default) | Volatile |

---

## Drift Thresholds

| Drift % | Status | Severity (Volatile) | Severity (Stable) |
|---------|--------|---------------------|-------------------|
| 0% | OK | None | None |
| <5% | Minor | Low | Medium |
| 5-15% | Moderate | Medium | High |
| 15-25% | Major | High | Critical |
| >25% | Critical | Critical | Critical |

---

## Examples

### Verify S3 Storage
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

### Update Python File Count
```bash
python scripts/monitoring/dims_cli.py update --category code_base --metric python_files
```

### View Documentation Growth
```bash
python scripts/monitoring/dims_cli.py history documentation.markdown_files --days 90
```

### Weekly Full Refresh
```bash
#!/bin/bash
cd /Users/ryanranft/nba-simulator-aws
python scripts/monitoring/dims_cli.py snapshot
python scripts/monitoring/dims_cli.py verify --update
python scripts/monitoring/dims_cli.py generate
python scripts/monitoring/dims_cli.py cache cleanup
git add inventory/metrics.yaml docs/MASTER_DATA_INVENTORY.md docs/DATA_COLLECTION_INVENTORY.md
git commit -m "Update data inventory metrics"
```

---

## Files & Locations

### Configuration
- **Config:** `inventory/config.yaml`
- **Metrics:** `inventory/metrics.yaml`
- **Cache:** `inventory/cache/`
- **Snapshots:** `inventory/historical/`

### Generated Outputs
- **Master Inventory:** `docs/MASTER_DATA_INVENTORY.md`
- **Collection Inventory:** `docs/DATA_COLLECTION_INVENTORY.md`
- **JSON Export:** `inventory/metrics.json`

### Code
- **CLI:** `scripts/monitoring/dims_cli.py`
- **Core Module:** `scripts/monitoring/dims/core.py`
- **Cache Module:** `scripts/monitoring/dims/cache.py`
- **Output Module:** `scripts/monitoring/dims/outputs.py`

---

## Troubleshooting

### Command Times Out
- Increase timeout in `inventory/config.yaml`
- Or disable slow metrics (e.g., `local_data.espn_size_gb`)

### Metric Not Updating
- Check if metric enabled: `enabled: true` in config
- Test command manually
- Check parse_type matches output

### Cache Not Working
- Verify `cache.enabled: true` in config
- Check `inventory/cache/` directory exists
- Run `dims_cli.py cache info`

### Wrong Drift Severity
- Adjust thresholds in `inventory/config.yaml` under `verification.thresholds`
- Or change metric categorization (stable vs volatile)

---

## Quick Tips

✅ **Run verify weekly** to catch metric drift early
✅ **Use --update** to automatically sync documented values
✅ **Create snapshots** before major changes
✅ **Check cache info** if metrics seem stale
✅ **Cleanup cache** monthly to remove expired entries

⚠️ **Don't** manually edit `inventory/metrics.yaml` (use CLI)
⚠️ **Don't** commit cache files to git (already in .gitignore)
⚠️ **Don't** enable all features at once (use toggles incrementally)

---

**Full Documentation:** `docs/DIMS_IMPLEMENTATION_SUMMARY.md`
**Help:** `python scripts/monitoring/dims_cli.py --help`
