## 📋 Phase README Alignment Workflow

**Purpose:** Ensure phase-specific READMEs stay aligned with the project vision defined in the main README.md

**Key principle:** The **main README.md is the single source of truth** for the project vision. Phase READMEs explain how their work enables that vision.

**When to use:**
- When completing a phase (required before marking ✅ COMPLETE)
- When updating the main README vision (propagate to relevant phases)
- Monthly documentation review (Workflow #20)
- Before major releases or presentations

---

## Validation Checklist

When validating a phase README against main README, check these areas:

### 1. Temporal Precision Alignment

**Main README defines:**
- Millisecond precision for play-by-play era (~1996-present)
- Simulation-based reconstruction for pre-play-by-play era (1946-1996)

**Phase README must:**
- [ ] Use same date ranges for temporal precision capabilities
- [ ] Correctly describe which data periods get millisecond precision vs simulation
- [ ] Reference main README for simulation methodology details
- [ ] Not claim precision capabilities that don't align with main README

**Common mistakes:**
- Stating "2020-2025: millisecond precision" when it's available for entire play-by-play era
- Claiming minute-level precision when wall clock + game clock enables millisecond precision
- Not mentioning simulation techniques for pre-play-by-play data

**Example - Incorrect:**
```markdown
Temporal precision levels:
- 2020-2025: Millisecond precision (NBA Live API)
- 1993-2019: Minute-level precision
- 1946-1992: Game-level aggregates
```

**Example - Correct:**
```markdown
Temporal precision by data availability:

**Play-by-play data available (~1996-present):**
- Millisecond-precision reconstruction
- Method: Wall clock timestamps + game clock alignment

**Box score data only (1946-1996):**
- Simulation-based temporal reconstruction
- Method: Econometric + nonparametric simulation (see main README)
```

### 2. Data Tracking (Use DIMS, Not Static Numbers)

**Phase READMEs must:**
- [ ] Use DIMS commands to show current S3 metrics
- [ ] Provide code snippets: `python scripts/monitoring/dims_cli.py verify --category s3_storage`
- [ ] Reference `inventory/metrics.yaml` for current counts
- [ ] Show historical baselines (e.g., "Oct 2024: 146,115 files")
- [ ] Link to Workflow #56 (DIMS Management) for complete tracking

**Do NOT use:**
- Static file count tables that will become stale
- Hardcoded "current total" numbers
- Phrases like "Live - Query S3 for current count" without providing the actual command

**Example - Incorrect:**
```markdown
| Milestone | Files | Size |
|-----------|-------|------|
| Current Total | 172,719* | 118 GB* |
```

**Example - Correct:**
```markdown
**Get current S3 metrics (always up-to-date):**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**Historical milestones:**
- Oct 2024: 146,115 files, 119 GB (baseline)
- Oct 2025: +25,323 files (ADCE growth)
```

### 3. Project Vision Alignment

**Phase READMEs must:**
- [ ] Explicitly state how the phase enables the main README vision
- [ ] Reference specific sections of main README (e.g., "Main README: Lines 49-87")
- [ ] Use consistent terminology (econometric causal inference, nonparametric, hybrid simulation)
- [ ] Link to main README with anchors: `[main README](../../../README.md#simulation-methodology)`

**Recommended structure:**
Add a "How This Phase Enables the Vision" section that explains:
1. What data/infrastructure this phase provides
2. Which simulation techniques from main README depend on it
3. Specific examples of capabilities enabled

**Example:**
```markdown
## How Phase 0.1 Data Enables the Simulation Vision

This phase collects the foundational temporal data that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this data enables:**

### 1. Temporal Panel Data Structure
- Player-game-possession observations with exact timestamps
- Wall clock + game clock alignment for millisecond precision

### 2. Econometric Causal Inference (Main README: Lines 49-87)
From this data, we estimate:
- Points Per Possession (PPP) using panel data regression
- Instrumental variables to address endogeneity
- Treatment effects of offensive plays vs defensive schemes

### 3. Nonparametric Event Modeling (Main README: Lines 88-97)
From this data, we build empirical distributions:
- Technical fouls (kernel density estimation)
- Injuries (bootstrap resampling)
- Momentum shifts (changepoint detection)
```

### 4. Methodology References

**Phase READMEs must:**
- [ ] Reference "econometric + nonparametric simulation" not just "simulation"
- [ ] Mention specific techniques: panel data regression, IV estimation, kernel density, bootstrap
- [ ] Link to main README for complete methodology
- [ ] Use correct terminology (PPP, treatment effects, empirical distributions)

**Do NOT:**
- Create simplified/different methodology descriptions in phase READMEs
- Contradict main README's approach (e.g., saying "Monte Carlo" when main README says "hybrid econometric + nonparametric")
- Leave vision references vague ("see project vision doc")

### 5. Cost & Resource Alignment

**Phase READMEs must:**
- [ ] Match cost estimates in main README (if main README provides them)
- [ ] Use same AWS resource names (S3 bucket, RDS database, etc.)
- [ ] Align timeline estimates with PROGRESS.md

### 6. Cross-References Work

**Validate all links:**
- [ ] Links to main README work: `[main README](../../../README.md)`
- [ ] Links to PROGRESS.md work: `[PROGRESS.md](../../PROGRESS.md)`
- [ ] Links to workflows work: `[Workflow #XX](../claude_workflows/workflow_descriptions/XX_name.md)`
- [ ] Links to other phases work

**Test links:**
```bash
# From the phase README directory, verify links resolve
cd docs/phases/phase_0/0.1_initial_data_collection
ls ../../../README.md  # Should exist
```

---

## Integration with Other Workflows

### Workflow #14 (Session End) - Optional Check

**When to run:** If you modified a phase README during the session

**At session end:**
```bash
# Check if phase README changes align with main README
# 1. Read main README project vision section
# 2. Read modified phase README
# 3. Verify terminology, dates, methodology match
```

**If misalignment found:** Fix before committing, or create TODO for next session

### Workflow #20 (Maintenance Schedule) - Monthly Validation

**When:** First Monday of each month

**Tasks:**
1. Read main README vision section (lines 1-400)
2. For each phase marked ✅ COMPLETE in PROGRESS.md:
   - Read phase README
   - Check temporal precision statements
   - Verify DIMS integration (not static numbers)
   - Check vision alignment section exists
   - Test cross-reference links
3. Create issues for any misalignments found
4. Update phase READMEs to match main README

### Workflow #52 (Phase Completion) - Required Validation

**When:** Before marking a phase ✅ COMPLETE in PROGRESS.md

**Required steps:**
1. Run full validation checklist (see above)
2. Ensure phase README explains how it enables main README vision
3. Verify all data tracking uses DIMS (no static tables)
4. Test all cross-reference links work
5. Get user confirmation that vision alignment is accurate

**Do NOT mark phase complete** until phase README aligns with main README.

---

## Common Scenarios

### Scenario 1: Main README Vision Updated

**Situation:** User updates the simulation methodology in main README.md

**Steps:**
1. Identify which phases are affected by the vision change
2. For each affected phase:
   - Read phase README
   - Update "How This Phase Enables Vision" section
   - Update any methodology references
   - Update temporal precision if changed
3. Commit with message: "docs: Align phase READMEs with updated main README vision"

### Scenario 2: Completing a New Phase

**Situation:** Phase 2.3 work is complete, ready to mark ✅ COMPLETE

**Before marking complete:**
1. Read main README vision (lines 1-400)
2. Read Phase 2.3 README
3. Check validation checklist (all 6 areas above)
4. If misalignments found:
   - Fix temporal precision statements
   - Add DIMS integration
   - Add "How This Phase Enables Vision" section
   - Update methodology references
5. Commit phase README fixes
6. Then mark phase ✅ COMPLETE in PROGRESS.md

### Scenario 3: User Highlights Phase README Inconsistency

**Situation:** User says "Phase 0.1 README temporal precision is outdated with main README"

**Steps:**
1. Read main README temporal precision section
2. Read Phase 0.1 README temporal precision section
3. Identify specific misalignments:
   - Wrong date ranges?
   - Incorrect precision capabilities?
   - Missing simulation methodology?
4. Update Phase 0.1 README to match main README
5. Check if other phases have same issue
6. Create Workflow #57 validation as future prevention

### Scenario 4: Monthly Documentation Review

**Situation:** First Monday of month, running Workflow #20

**Task: Validate all phase READMEs**

**Steps:**
1. List all completed phases from PROGRESS.md
2. For each phase:
   ```bash
   # Read phase README
   # Compare to main README vision
   # Run validation checklist
   # Document misalignments
   ```
3. Prioritize fixes:
   - Critical: Incorrect temporal precision or methodology
   - Important: Missing vision alignment section
   - Nice-to-have: Static numbers instead of DIMS
4. Fix critical/important issues
5. Create TODOs for nice-to-have improvements

---

## Troubleshooting

**Problem: Phase README contradicts main README**

**Example:** Phase says "minute-level precision" but main README says "millisecond precision"

**Solution:**
1. Main README is source of truth
2. Update phase README to match main README
3. Add comment explaining: "See [main README](../../../README.md) for complete temporal precision details"

**Problem: Phase README has static file counts**

**Example:** Phase README says "172,719 files" in a table

**Solution:**
1. Replace table with DIMS commands
2. Move static numbers to "Historical milestones" section
3. Add: "For current metrics, run: `python scripts/monitoring/dims_cli.py verify --category s3_storage`"
4. Link to Workflow #56 (DIMS Management)

**Problem: Phase README doesn't explain how it enables vision**

**Example:** Phase just describes what was done, not why it matters

**Solution:**
1. Add "How This Phase Enables the Vision" section
2. Reference specific main README sections
3. List which simulation techniques depend on this phase's outputs
4. Give concrete examples of enabled capabilities

**Problem: Broken cross-reference links**

**Example:** `[main README](../../README.md)` doesn't work (wrong depth)

**Solution:**
1. Determine correct relative path:
   - From `docs/phases/phase_0/0.1_initial_data_collection/README.md`
   - To `README.md`
   - Path: `../../../README.md`
2. Test link works:
   ```bash
   cd docs/phases/phase_0/0.1_initial_data_collection
   ls ../../../README.md  # Should exist
   ```
3. Fix all similar links

**Problem: Methodology terminology differs from main README**

**Example:** Phase says "machine learning" but main README says "econometric causal inference + nonparametric event modeling"

**Solution:**
1. Use main README's precise terminology
2. Add specific techniques: panel data regression, IV estimation, kernel density estimation
3. Don't oversimplify or use generic terms like "ML" or "AI"

---

## Validation Script (Future Enhancement)

**Potential automation:**

Create `scripts/maintenance/validate_phase_readme.py` that checks:
- Temporal precision date ranges match main README
- Phase README contains "How This Phase Enables Vision" section
- No static file count tables (should use DIMS commands)
- All cross-reference links resolve
- Methodology terminology matches main README

**Usage:**
```bash
# Validate specific phase
python scripts/maintenance/validate_phase_readme.py --phase 0.1

# Validate all phases
python scripts/maintenance/validate_phase_readme.py --all

# Show diff
python scripts/maintenance/validate_phase_readme.py --diff
```

**Output:**
```
Phase 0.1 README Validation:
✅ Temporal precision aligns with main README
✅ DIMS integration present
✅ Vision alignment section exists
❌ Broken link: ../../README.md (should be ../../../README.md)
⚠️  Methodology uses "simulation" (should be "econometric + nonparametric simulation")
```

---

## Success Criteria

Phase README is aligned when:

- [ ] Temporal precision statements match main README date ranges and capabilities
- [ ] Data tracking uses DIMS commands, not static tables
- [ ] "How This Phase Enables Vision" section exists and references main README
- [ ] Methodology terminology matches main README (econometric, nonparametric, etc.)
- [ ] All cross-reference links work (main README, PROGRESS.md, other phases)
- [ ] Cost estimates align with main README and PROGRESS.md
- [ ] No contradictions with main README vision

**When all criteria met:** Phase README is accurate and can be used as reliable reference.

---

## Related Workflows

- **Workflow #14 (Session End):** Optional check after modifying phase READMEs
- **Workflow #20 (Maintenance Schedule):** Monthly validation of all phase READMEs
- **Workflow #52 (Phase Completion):** Required validation before marking phase complete
- **Workflow #56 (DIMS Management):** Data tracking tool for dynamic metrics

---

**Last Updated:** October 23, 2025
**Status:** ✅ Active - Use when completing phases or updating vision
**Integration:** Required for phase completion, monthly for maintenance
