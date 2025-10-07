# Workflow #38: Overnight Scraper Handoff Protocol

**Purpose:** Document and track overnight scraping jobs for seamless session continuation

**When to use:**
- At end of session when overnight scrapers are running
- At start of next session to check scraper status
- When documenting long-running background jobs

---

## End of Session (Before Signing Off)

### 1. Document Running Scrapers

**Check what's running:**
```bash
ps aux | grep -E "(scrape|overnight)" | grep -v grep
```

**For each running scraper, document:**
- Process ID (PID)
- Script name
- Start time
- Expected completion time
- Output location
- S3 upload location (if applicable)
- Log file location

### 2. Update PROGRESS.md "Current Session Context"

**Template:**
```markdown
**Last session ended:** [DATE]
**Last completed:** [WHAT WAS FINISHED]
**Overnight jobs running:**
  - [SCRAPER_NAME]: PID [PID], started [TIME], ETA [TIME]
    - Output: [LOCAL_PATH]
    - S3: [S3_PATH]
    - Log: [LOG_PATH]
**Next to work on:** Check scraper status, validate results, [NEXT_TASK]
**Phase status:** [CURRENT_STATUS]
```

### 3. Create Handoff Note (if needed)

**For complex scraping jobs, create:**
```bash
# Create handoff document
cat > docs/SCRAPER_HANDOFF_$(date +%Y%m%d).md << 'EOF'
# Overnight Scraper Handoff - [DATE]

## Running Jobs

### [Job Name]
- **PID:** [PID]
- **Started:** [TIME]
- **Expected completion:** [ETA]
- **Purpose:** [WHY RUNNING]
- **Configuration:** [KEY SETTINGS]
- **Output:** [WHERE TO FIND RESULTS]
- **Next steps:** [WHAT TO DO WHEN COMPLETE]

## Validation Checklist (For Next Session)
- [ ] Check process still running: `ps aux | grep [PID]`
- [ ] Review log for errors: `tail -100 [LOG_FILE]`
- [ ] Validate output files created: `ls -lh [OUTPUT_DIR]`
- [ ] Check S3 uploads (if applicable): `aws s3 ls [S3_PATH]`
- [ ] Review data quality: [VALIDATION_STEPS]

## If Scraper Failed
- [ ] Check error logs: `grep -i error [LOG_FILE]`
- [ ] Review last successful operation
- [ ] Determine restart point
- [ ] Document issue in TROUBLESHOOTING.md

## Known Issues / Limitations
- [LIST ANY CONSTRAINTS OR KNOWN ISSUES]
EOF
```

### 4. Update CHANGELOG.md (if significant)

**Add entry for overnight job:**
```markdown
### Running - [Job Name]
**Started:** [DATE/TIME]
**Status:** In progress (overnight job)
**Expected completion:** [ETA]
**Purpose:** [DESCRIPTION]
**Note:** See SCRAPER_HANDOFF_[DATE].md for details
```

---

## Start of Next Session (Morning After)

### 1. Check Scraper Status

**Is it still running?**
```bash
ps aux | grep [PID]
```

**Check log for progress:**
```bash
tail -100 [LOG_FILE]
# Or for specific patterns:
tail -500 [LOG_FILE] | grep -E "(Progress|Error|Complete|Season)"
```

**Check output files:**
```bash
ls -lh [OUTPUT_DIR] | tail -20
# Count files created:
find [OUTPUT_DIR] -type f -name "*.json" | wc -l
```

### 2. Determine Status

**If completed successfully:**
- ✅ Mark job as complete in PROGRESS.md
- ✅ Update CHANGELOG.md with results
- ✅ Run validation checks
- ✅ Document final stats (files created, data size, etc.)

**If still running:**
- 🔄 Estimate remaining time
- 🔄 Update PROGRESS.md with new ETA
- 🔄 Continue with other tasks

**If failed/stopped:**
- ❌ Review error logs
- ❌ Determine failure point
- ❌ Document issue
- ❌ Plan restart strategy

### 3. Validation Checks

**For NBA API scrapers:**
```bash
# Check file counts per category
for dir in /tmp/nba_api_comprehensive/*/; do
  echo "$(basename $dir): $(find $dir -type f | wc -l) files"
done

# Check data sizes
du -sh /tmp/nba_api_comprehensive/*

# Check for errors in logs
grep -i "error\|fail\|exception" [LOG_FILE] | head -20

# Validate JSON files
find [OUTPUT_DIR] -name "*.json" -type f | head -5 | while read file; do
  echo "Checking $file..."
  python -m json.tool "$file" > /dev/null && echo "✅ Valid" || echo "❌ Invalid"
done
```

**For S3 uploads:**
```bash
# Check S3 upload status
aws s3 ls s3://nba-sim-raw-data-lake/[PREFIX]/ --recursive | tail -20

# Count S3 objects
aws s3 ls s3://nba-sim-raw-data-lake/[PREFIX]/ --recursive | wc -l

# Check recent uploads
aws s3 ls s3://nba-sim-raw-data-lake/[PREFIX]/ --recursive | tail -10
```

### 4. Update Documentation

**Update PROGRESS.md:**
```markdown
**Last session ended:** [PREVIOUS_DATE]
**Last completed:** [SCRAPER_NAME] overnight run completed
  - Files created: [COUNT]
  - Data size: [SIZE]
  - Coverage: [WHAT WAS SCRAPED]
  - S3 location: [S3_PATH]
**Next to work on:** [NEXT_TASK based on results]
```

**Update CHANGELOG.md:**
```markdown
### Completed - [Job Name]
**Completed:** [DATE/TIME]
**Duration:** [HOURS]
**Results:**
- Files created: [COUNT]
- Data size: [SIZE]
- Coverage: [DETAILS]
- Output: [LOCATIONS]
**Status:** ✅ Success / ⚠️ Partial / ❌ Failed
```

---

## Common Overnight Job Types

### NBA API Comprehensive Scraper
**Check command:**
```bash
ps aux | grep scrape_nba_api_comprehensive
```

**Key locations:**
- Output: `/tmp/nba_api_comprehensive/`
- S3: `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`
- Logs: `/Users/ryanranft/nba-simulator-aws/logs/nba_api_comprehensive_*/`

**Validation:**
- Check seasons processed
- Verify endpoint coverage (league_dashboards, boxscores_advanced, tracking, etc.)
- Validate JSON structure
- Confirm S3 uploads

### hoopR Comprehensive Scraper
**Check command:**
```bash
ps aux | grep scrape_hoopr
```

**Key locations:**
- Output: `/tmp/hoopr_nba_stats/`
- S3: `s3://nba-sim-raw-data-lake/hoopr_nba_stats/`
- Logs: `/Users/ryanranft/nba-simulator-aws/logs/hoopr_comprehensive_*/`

**Validation:**
- Check batch completion
- Verify data loader types (pbp, team_box, player_box, schedule)
- Check Polars DataFrame conversion
- Confirm S3 uploads

---

## Troubleshooting

### Scraper Stopped Unexpectedly

**Check system resources:**
```bash
# Check available memory
free -h

# Check disk space
df -h

# Check for OOM kills
dmesg | grep -i "killed process"
```

**Find restart point:**
```bash
# Check last successful file
ls -ltr [OUTPUT_DIR]/*/ | tail -20

# Check last log entry
tail -100 [LOG_FILE]

# Determine last season/batch processed
grep "Season\|Batch" [LOG_FILE] | tail -5
```

### S3 Upload Issues

**Check AWS credentials:**
```bash
aws sts get-caller-identity
```

**Check S3 permissions:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/
```

**Retry failed uploads:**
```bash
# Find files not in S3
find [LOCAL_DIR] -name "*.json" | while read file; do
  s3_key="[S3_PREFIX]/$(basename $file)"
  aws s3api head-object --bucket nba-sim-raw-data-lake --key "$s3_key" 2>/dev/null || echo "$file"
done
```

---

## Best Practices

1. **Always log PID and start time** - Easier to track and monitor
2. **Use nohup for overnight jobs** - Prevents termination on logout
3. **Redirect output to log files** - Capture all output for debugging
4. **Set reasonable timeouts** - Prevent infinite hangs
5. **Document expected completion** - Know when to check back
6. **Update PROGRESS.md before leaving** - Next session knows what to check
7. **Test validation commands** - Know how to verify success
8. **Plan for failure scenarios** - Document recovery steps

---

*Last updated: October 6, 2025*
