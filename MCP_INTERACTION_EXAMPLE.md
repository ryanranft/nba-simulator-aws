# MCP Interaction Example: How to Use the Temporal Build Request

**Purpose:** Step-by-step guide for using the MCP request documents to generate an implementation plan
**Created:** October 20, 2025
**Audience:** User providing documents to MCP server

---

## Overview

This guide shows you how to use the MCP request documents to get a comprehensive implementation plan for completing the temporal data build.

**What You Have:**
1. `MCP_TEMPORAL_BUILD_REQUEST.md` - Comprehensive project context and requirements (~1,000 lines)
2. `MCP_SUPPORTING_FILES_INDEX.md` - Index of all supporting files (~200 lines)
3. This file - Usage instructions

**What You'll Get:**
A detailed, actionable implementation plan with:
- Prioritized task sequencing
- Time and cost estimates
- Risk mitigation strategies
- Week-by-week roadmap

---

## Method 1: Direct MCP Server Interaction

### Step 1: Prepare Your Environment

```bash
# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Verify MCP server is available
# (Exact command depends on your MCP server setup)
```

### Step 2: Provide the Main Request to MCP

**Option A: Copy-paste the entire request**

```
I need you to analyze a complex software project and create a comprehensive
implementation plan. I'm providing a detailed request document that contains:

- Complete project context and vision
- Current state analysis (what's done, what's remaining)
- Detailed work inventory across 4 major workstreams
- Technical requirements and constraints
- Success criteria
- Specific requirements for the plan you should generate

Please read the following document carefully and generate the requested
implementation plan:

[PASTE CONTENTS OF MCP_TEMPORAL_BUILD_REQUEST.md HERE]
```

**Option B: If your MCP supports file reading**

```
Please read the file MCP_TEMPORAL_BUILD_REQUEST.md in the current directory
and generate the comprehensive implementation plan as specified in Section F
of that document.

Context: This is for completing a temporal panel data system for NBA basketball
analytics. The project is 60-80% complete; we need a detailed plan for the
remaining 8-12 weeks of work.
```

### Step 3: Provide Supporting Files Index (Optional)

```
For additional context, I'm also providing an index of all supporting files
you may want to reference:

[PASTE CONTENTS OF MCP_SUPPORTING_FILES_INDEX.md HERE]

You don't need to read all of these now, but they're available if you need
specific technical details while creating the plan.
```

### Step 4: Answer Any Clarifying Questions

The MCP may ask questions like:
- What's your preferred timeline (aggressive, realistic, comprehensive)?
- How many hours per week are available for implementation?
- Which success tier do you want to prioritize (MVC, Production Ready, Comprehensive)?

**Example Responses:**
```
Q: What's your preferred timeline?
A: Realistic timeline, prioritizing quality over speed. I can dedicate
   20-25 hours per week.

Q: Which success tier should I optimize for?
A: Focus on Minimum Viable Complete (Tier 1) first, with clear extension
   points to Production Ready (Tier 2) later.

Q: Should Basketball Reference scraping start immediately or wait?
A: Start in parallel with snapshot generation fixes. I can work on both
   simultaneously since they're independent.
```

### Step 5: Review and Iterate

Once the MCP generates the initial plan:

1. **Review the output** - Check if it matches the requested structure (Section F)
2. **Ask for clarifications** - If anything is unclear or missing
3. **Request adjustments** - If priorities need to change

**Example Follow-up:**
```
Thank you for the comprehensive plan! I have a few requests:

1. Can you add more detail to Week 3's "Storage System Implementation"?
   What specific files need to be created?

2. The time estimate for Basketball Reference Tier 1 seems aggressive.
   Can you add a risk buffer?

3. Can you create a one-page executive summary of the entire plan?
```

---

## Method 2: Structured Conversation Approach

If your MCP works better with conversational interaction, use this approach:

### Phase 1: Introduction

```
I'm working on a complex data engineering project for NBA basketball analytics.
I need your help creating a detailed implementation plan to finish the remaining
work (estimated 8-12 weeks).

The project is a temporal panel data system that enables querying NBA statistics
at any exact moment in time with millisecond precision. We're about 60-80%
complete.

I have a comprehensive briefing document (~1,000 lines) that contains:
- Full project context
- Current state analysis
- Remaining work inventory (4 major workstreams)
- Success criteria
- Specific requirements for the plan

Would you like me to provide the full document now, or would you prefer to
start with a summary?
```

### Phase 2: Context Delivery

**If MCP requests summary first:**
```
Summary:

Current State:
- 6 of 8 core phases complete
- 214 ML recommendations implemented
- Phase 2 snapshot generation 60% complete (4-6 hours remaining)
- 172,600 files in data lake (~122 GB)
- AWS infrastructure operational ($41.53/month)

Remaining Work (4 Workstreams):
1. Complete snapshot generation pipeline (4-6 hours)
2. Build additional data processors (8-10 weeks)
3. Expand Basketball Reference data collection (140-197 hours)
4. Multi-source data integration (28 hours)

I can now provide the full detailed document if you'd like, or answer
specific questions first.
```

**If MCP is ready for full document:**
```
Here's the complete request document:

[PASTE MCP_TEMPORAL_BUILD_REQUEST.md]
```

### Phase 3: Specify Output Format

```
Based on the request document, please generate an implementation plan with
this structure:

1. EXECUTIVE_SUMMARY.md (1-2 pages)
   - High-level plan, milestones, risks

2. PRIORITIZED_TASK_LIST.md (5-10 pages)
   - All tasks in execution order
   - Dependencies marked
   - Parallel work identified

3. DETAILED_WORKSTREAM_PLANS.md (20-40 pages)
   - Full breakdown of all 4 workstreams
   - Each task with time estimates, risks, success metrics

4. INTEGRATION_STRATEGY.md (5-10 pages)
   - How components fit together
   - Data flows and API contracts

5. WEEK_BY_WEEK_ROADMAP.md (10-15 pages)
   - Weekly milestones and decision points
   - Quality gates and rollback procedures

6. RESOURCE_PLAN.md (3-5 pages)
   - Time/cost projections
   - Testing and monitoring requirements

7. RISK_REGISTER.md (3-5 pages)
   - All risks with mitigation strategies

Can you generate these 7 documents?
```

### Phase 4: Refinement

After receiving the plan:

```
Thank you! This is a great start. A few refinement requests:

[Specific feedback on each section]

Also, can you provide:
1. A decision tree for "When should I skip to the next workstream vs.
   continue polishing current work?"
2. Alternative plans for aggressive vs. comprehensive timelines
3. A cost projection chart showing monthly AWS costs over the 12-week period
```

---

## Method 3: Batch File Processing

If your MCP supports batch processing multiple files:

### Create a Manifest File

```json
{
  "task": "Generate implementation plan for temporal data build completion",
  "input_files": [
    "MCP_TEMPORAL_BUILD_REQUEST.md",
    "MCP_SUPPORTING_FILES_INDEX.md",
    "PROGRESS.md",
    "docs/OPTION_2A_STATUS.md",
    "docs/phases/PHASE_9_INDEX.md"
  ],
  "output_format": "7 markdown documents as specified in request",
  "priorities": [
    "Minimum Viable Complete (Tier 1) first",
    "Quality over speed",
    "Stay within $150/month budget"
  ],
  "constraints": {
    "hours_per_week": 20,
    "budget_monthly": 150,
    "risk_tolerance": "low for data loss, medium for cost, high for timeline"
  }
}
```

### Submit to MCP

```bash
# Example - exact command depends on your MCP setup
mcp-cli process --manifest plan_request.json --output-dir implementation_plan/
```

---

## What to Expect in the Response

### Document 1: EXECUTIVE_SUMMARY.md

**Should contain:**
- Total time estimate (e.g., "12 weeks, 180 hours")
- Total cost estimate (e.g., "$42-48/month AWS")
- 5-7 major milestones
- Top 5 risks
- Go/no-go recommendation

**Example excerpt:**
```markdown
# Executive Summary: Temporal Data Build Completion Plan

## Overview
Complete the NBA temporal panel data system in 12 weeks with 4 parallel
workstreams, delivering Minimum Viable Complete in 3 weeks and Production
Ready in 10 weeks.

## Timeline
- Week 1-3: Minimum Viable Complete (14,798 games processed, Tier 1-2 data)
- Week 4-10: Production Ready (all processors, advanced metrics, ML integration)
- Week 11-12: Buffer and optimization

## Cost
- Current: $41.53/month
- Peak (Week 8): $48/month
- Steady-state: $43/month
- Within $150/month budget ✓

## Major Milestones
1. Week 1: Snapshot generation fixes complete
2. Week 3: All 14,798 games processed, stored in RDS
3. Week 5: Basketball Reference Tier 1-2 complete (350K records)
4. Week 8: Advanced metrics layer deployed
5. Week 10: ML models retrained with new features

## Top Risks
1. Basketball Reference blocking (likelihood: medium, impact: high)
   - Mitigation: Rate limiting, user-agent rotation, fallback to manual
2. Database performance degradation with 43M rows
   - Mitigation: Index optimization, query tuning, partitioning
...
```

### Document 2: PRIORITIZED_TASK_LIST.md

**Should contain:**
- All tasks numbered sequentially (e.g., Task 1.1, 1.2, 2.1...)
- Dependencies clearly marked
- Parallel tasks identified
- Critical path highlighted

**Example excerpt:**
```markdown
# Prioritized Task List

## Critical Path Tasks (Must complete in sequence)
□ 1.1: Fix substitution handling (3 hours) - BLOCKS: 1.2, 1.3, 1.4
□ 1.2: Improve parser coverage (3 hours) - REQUIRES: 1.1, BLOCKS: 1.3
□ 1.3: Test on 10 games (1 hour) - REQUIRES: 1.1, 1.2, BLOCKS: 1.4
□ 1.4: Implement database save (2 hours) - REQUIRES: 1.3, BLOCKS: 1.5
□ 1.5: Scale to full dataset (1.5 hours) - REQUIRES: 1.4, BLOCKS: 2C.1

## Parallel Track A (Can start immediately)
□ 3.1: Set up Basketball Reference scraper (2 hours)
□ 3.2: Implement Tier 1 - Advanced box scores (4 hours) - REQUIRES: 3.1
□ 3.3: Implement Tier 1 - Play-by-play (5 hours) - REQUIRES: 3.2
...

## Parallel Track B (Can start after Task 1.5)
□ 2C.1: Design storage schema (3 hours) - REQUIRES: 1.5
□ 2C.2: Implement RDS batch insert (4 hours) - REQUIRES: 2C.1
...
```

### Document 3: DETAILED_WORKSTREAM_PLANS.md

**Should contain:**
- For each task: description, files, time estimate, dependencies, risks, metrics
- Code examples where applicable
- Testing requirements

**Example excerpt:**
```markdown
# Workstream 1: Complete Phase 2 Snapshot Generation

## Task 1.1: Fix Substitution Handling

### Description
Modify `game_state_tracker.py` to build lineups from substitution events
instead of inferring from early plays. Start with empty lineups and populate
from first 5 substitutions per team.

### Files to Modify
1. `scripts/pbp_to_boxscore/game_state_tracker.py`
   - Add method: `build_lineup_from_substitutions(events)` (~40 lines)
   - Modify method: `process_event(event)` to use new logic (~20 lines)
   - Remove method: `infer_starting_lineup()` (delete ~30 lines)

2. `scripts/pbp_to_boxscore/rds_pbp_processor.py`
   - Remove call to `get_starting_lineups()` (~5 lines)
   - Pass full event list to tracker initialization (~10 lines)

3. Create test: `tests/test_substitution_handling.py` (~150 lines)
   - Test: lineups stay at 5 players
   - Test: substitutions work correctly
   - Test: edge case - player ejection

### Time Estimate
- Optimistic: 1.5 hours
- Realistic: 2.5 hours
- Pessimistic: 4 hours
- **3-Point Estimate: 2.7 hours**

### Dependencies
- **Prerequisites:** None (can start immediately)
- **Blocks:** Tasks 1.2, 1.3, 1.4, 1.5 (all subsequent Workstream 1 tasks)

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Some games lack substitution events | Low | Medium | Implement fallback to old logic |
| Players ejected mid-game | Medium | Low | Handle as special substitution type |
| Testing reveals edge cases | High | Low | Add 30min buffer for edge case fixes |

### Success Metrics
- [ ] All test games maintain 5 players per team (100% pass)
- [ ] Unit tests pass (13/13)
- [ ] No "lineup has X players" warnings in logs
- [ ] Validated on 3 diverse test games
```

### Document 4-7: INTEGRATION_STRATEGY, ROADMAP, RESOURCE_PLAN, RISK_REGISTER

Similar detailed breakdowns for:
- How systems integrate
- Week-by-week schedule
- Resource allocation
- Comprehensive risk analysis

---

## Tips for Getting the Best Results

### 1. Be Specific About Your Constraints

```
Good:
"I can work 20-25 hours per week, mostly evenings and weekends. I want to
deliver Minimum Viable Complete in 3 weeks if possible."

Bad:
"I want this done soon."
```

### 2. Clarify Your Priorities

```
Good:
"Priority 1: Get snapshot generation working for all 14,798 games (Workstream 1).
Priority 2: Add Basketball Reference Tier 1-2 data (partial Workstream 3).
Priority 3: Everything else can wait."

Bad:
"I want everything."
```

### 3. Specify Your Risk Tolerance

```
Good:
"Low risk tolerance for data corruption or loss. Medium tolerance for cost
overruns within budget. High tolerance for timeline slips - quality matters
more than speed."

Bad:
"Just make it work."
```

### 4. Ask for Alternatives

```
"Please provide 3 alternative plans:
1. Aggressive: Minimum Viable Complete in 2 weeks (cutting corners where safe)
2. Balanced: Production Ready in 10 weeks (recommended approach)
3. Comprehensive: Everything including optional tiers in 16 weeks"
```

### 5. Request Specific Output Formats

```
"For the week-by-week roadmap, please include:
- Gantt chart (text-based)
- Daily task breakdowns for Week 1 (since I'm starting immediately)
- High-level weekly summaries for Weeks 2-12"
```

---

## Follow-Up Questions to Ask

### After Receiving Initial Plan

1. **Clarifications:**
   - "Can you explain why Task X must come before Task Y?"
   - "What exactly does 'validation' mean in Task 3.4?"
   - "How do I know when Workstream 2C is complete?"

2. **Risk Deep-Dives:**
   - "What's the contingency plan if Basketball Reference blocks our scraper?"
   - "If the snapshot generation fails at scale, how do we debug?"
   - "What's the rollback procedure for database schema changes?"

3. **Resource Planning:**
   - "Can you break down the $48/month peak cost by service?"
   - "Which weeks are most time-intensive?"
   - "When should I schedule code reviews or pair programming?"

4. **Integration Details:**
   - "How does the snapshot data flow into the ML models?"
   - "What APIs need to be defined between components?"
   - "Are there any circular dependencies in the plan?"

### To Refine the Plan

```
"Thank you for the comprehensive plan. I'd like to adjust:

1. Move Basketball Reference Tier 3 up in priority (before Tier 2)
2. Add a 1-week buffer after Week 8 for testing
3. Break down Week 1 into daily tasks since I'm starting Monday
4. Add more detail on the verification step (Task 1.4)

Can you regenerate the affected sections?"
```

---

## Troubleshooting

### "The MCP doesn't understand the context"

**Solution:** Simplify the ask
```
"I'm providing a detailed request document. Please:
1. Read the entire document
2. Pay special attention to Section F (what I need you to generate)
3. Ask me any clarifying questions before starting
4. Then generate the 7 documents as specified"
```

### "The output is too high-level"

**Solution:** Request more detail
```
"This is a good start, but I need more granularity. For each task, please add:
- Specific files to create/modify (with line counts)
- Code snippets or pseudocode where helpful
- Step-by-step sub-tasks
- Acceptance criteria (how to know it's done)"
```

### "The timeline seems unrealistic"

**Solution:** Provide feedback
```
"The 2-week timeline for Workstream 2 seems aggressive. Based on my experience:
- Task 2C takes 2 days, not 4 hours (database changes are slow)
- Task 2D needs 2 weeks, not 3 days (15 metrics to implement)

Can you recalculate with more realistic estimates?"
```

### "The plan is missing something important"

**Solution:** Specify the gap
```
"The plan covers implementation well, but I don't see:
1. Testing strategy (unit, integration, performance tests)
2. Monitoring/alerting setup
3. Documentation requirements
4. Deployment/rollout procedures

Can you add sections for these?"
```

---

## Next Steps After You Get the Plan

### 1. Review and Validate

- [ ] Read the entire plan thoroughly
- [ ] Check for completeness (all 4 workstreams covered?)
- [ ] Verify dependencies make sense
- [ ] Ensure timeline is realistic

### 2. Get Approval (If Needed)

- [ ] Share executive summary with stakeholders
- [ ] Get buy-in on timeline and budget
- [ ] Discuss risks and mitigation strategies

### 3. Set Up Tracking

- [ ] Create GitHub project or Trello board
- [ ] Add all tasks with estimates
- [ ] Set up milestones and deadlines
- [ ] Create calendar reminders for checkpoints

### 4. Start Execution

- [ ] Begin with Task 1.1 (the first critical path task)
- [ ] Track time spent vs. estimated
- [ ] Update progress daily or weekly
- [ ] Adjust plan as you learn more

### 5. Regular Reviews

- [ ] Weekly: Review progress, adjust timeline if needed
- [ ] Monthly: Reassess priorities, celebrate milestones
- [ ] Continuous: Update risk register as risks change

---

## Example Success Story

```
Week 0 (Planning):
✓ Provided MCP request documents
✓ Received comprehensive 7-document plan
✓ Reviewed and refined plan
✓ Set up task tracking in GitHub

Week 1 (Execution):
✓ Fixed substitution handling (2.5 hrs - on target!)
✓ Improved parser coverage to 87% (2 hrs - beat estimate!)
✓ Started Basketball Reference Tier 1 scraper (parallel work)

Week 2:
✓ Tested on 10 games, all passed
✓ Implemented database save functionality
✓ Scaled to 100 games (validation)
✓ Continued Basketball Reference scraping

Week 3:
✓ Scaled to all 14,798 games (SUCCESS!)
✓ Completed Basketball Reference Tier 1
✓ Minimum Viable Complete achieved!

Result: 3 weeks, exactly as planned. Now continuing to Production Ready tier.
```

---

**Document Version:** 1.0
**Created:** October 20, 2025
**Purpose:** Guide for using MCP request documents effectively
**Questions?** Review MCP_TEMPORAL_BUILD_REQUEST.md for full context
