# 9.3: Add Prompt Monitoring and Logging with Opik

**Sub-Phase:** 9.3 (Monitoring)
**Parent Phase:** [Phase 9: Monitoring & Observability](../PHASE_9_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** 🟡 IMPORTANT
**Implementation ID:** rec_051

---

## Overview

Add a prompt monitoring layer on top of LLM Twin’s inference pipeline using Opik from Comet ML. This enables analysis, debugging, and better understanding of the system.

**Key Capabilities:**
- Wrap the LLM and RAG steps with the @track decorator from Opik
- Use Opik to monitor user queries, enriched prompts, and generated answers
- Attach metadata and tags to the traces.

**Impact:**
Improved analysis, debugging, and understanding of the LLM Twin system, enables rapid error pinpointing with trace logging, quick metric feedback.

---

## Quick Start

```python
from implement_rec_051 import ImplementAddPromptMonitoringAndLoggingWithOpik

# Initialize implementation
impl = ImplementAddPromptMonitoringAndLoggingWithOpik()
impl.setup()

# Execute implementation
results = impl.execute()

print(f"Implementation complete: {results}")
```

---

## Architecture

### Implementation Steps

1. Step 1: Install the Opik and Comet ML libraries.
2. Step 2: Wrap the LLM and RAG steps with the @track decorator.
3. Step 3: Attach metadata and tags to the traces using the update() method.
4. Step 4: Analyze the traces in the Opik dashboard.

---

## Implementation Files

| File | Purpose |
|------|---------|
| **implement_rec_051.py** | Main implementation |
| **test_rec_051.py** | Test suite |
| **STATUS.md** | Implementation status |
| **RECOMMENDATIONS_FROM_BOOKS.md** | Source book recommendations |
| **IMPLEMENTATION_GUIDE.md** | Detailed implementation guide |

---

## Configuration

```python
# Configuration example
config = {
    "enabled": True,
    "mode": "production",
    # Add specific configuration parameters
}

impl = ImplementAddPromptMonitoringAndLoggingWithOpik(config=config)
```

---

## Performance Characteristics

**Estimated Time:** 8 hours

---

## Dependencies

**Prerequisites:**
- Build Business Microservice with FastAPI
- Deploy LLM Microservice using AWS SageMaker

**Enables:**
- Enhanced system capabilities
- Improved prediction accuracy
- Better maintainability

---

## Usage Examples

### Example 1: Basic Usage

```python
# Basic implementation
from implement_rec_051 import ImplementAddPromptMonitoringAndLoggingWithOpik

impl = ImplementAddPromptMonitoringAndLoggingWithOpik()
impl.setup()
results = impl.execute()
```

---

## Integration with Other Sub-Phases

This recommendation integrates with:
- Phase 9 components
- Cross-phase dependencies as specified

---

## Testing

```bash
# Run test suite
cd /Users/ryanranft/nba-simulator-aws/docs/phases/phase_9/9.0003_add_prompt_monitoring_and_logging_with_opik
python test_rec_051.py -v
```

---

## Troubleshooting

**Common Issues:**
- See IMPLEMENTATION_GUIDE.md for detailed troubleshooting

---



---

## How This Phase Enables the Simulation Vision

This phase provides critical infrastructure that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference Foundation

This phase supports econometric causal inference:

**Panel data infrastructure:**
- Enables fixed effects and random effects estimation
- Supports instrumental variables (IV) regression
- Facilitates propensity score matching

**Causal identification:**
- Provides data for difference-in-differences estimation
- Enables regression discontinuity designs
- Supports synthetic control methods

**Treatment effect estimation:**
- Heterogeneous treatment effects across subgroups
- Time-varying treatment effects in dynamic panels
- Robustness checks and sensitivity analysis

### 2. Nonparametric Event Modeling (Distribution-Free)

This phase supports nonparametric event modeling:

**Empirical distributions:**
- Kernel density estimation for irregular events
- Bootstrap resampling from observed data
- Empirical CDFs without parametric assumptions

**Distribution-free methods:**
- No assumptions on functional form
- Direct sampling from empirical distributions
- Preserves tail behavior and extreme events

### 3. Context-Adaptive Simulations

Using this phase's capabilities, simulations adapt to:

**Game context:**
- Score differential and time remaining
- Playoff vs. regular season
- Home vs. away venue

**Player state:**
- Fatigue levels and minute load
- Recent performance trends
- Matchup-specific adjustments

### 4. Integration with Main README Methodology

**Panel data regression (Main README: Lines 81-87):**
- This phase supports panel data regression infrastructure

**Nonparametric validation (Main README: Line 116):**
- This phase supports nonparametric validation infrastructure

**Monte Carlo simulation (Main README: Line 119):**
- This phase supports Monte Carlo simulation infrastructure

**See [main README](../../../README.md) for complete methodology.**

---

## Related Documentation

- **[STATUS.md](STATUS.md)** - Implementation status
- **[RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md)** - Source recommendations
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Detailed guide
- **[Phase 9 Index](../PHASE_9_INDEX.md)** - Parent phase overview

---

## Navigation

**Return to:** [Phase 9: Monitoring & Observability](../PHASE_9_INDEX.md)

---

**Last Updated:** October 19, 2025
**Maintained By:** NBA Simulator AWS Team
**Source:** LLM Engineers Handbook
