# 5.126: Integrate Recent Form as a Covariate

**Sub-Phase:** 5.126 (ML)
**Parent Phase:** [Phase 5: Machine Learning](../PHASE_5_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** 🟡 IMPORTANT
**Implementation ID:** rec_168

---

## Overview

Model recent team form by scoring a team's performance in the last 5 games, giving 1 point for a victory, 0 for a draw, and -1 for a loss. Incorporate this form variable as a covariate in the model.

**Key Capabilities:**
- Form variable calculation, covariate integration, loop creation.

**Impact:**
Improved model accuracy by incorporating recent team performance.

---

## Quick Start

```python
from implement_rec_168 import ImplementIntegrateRecentFormAsACovariate

# Initialize implementation
impl = ImplementIntegrateRecentFormAsACovariate()
impl.setup()

# Execute implementation
results = impl.execute()

print(f"Implementation complete: {results}")
```

---

## Architecture

### Implementation Steps

1. Step 1: Create a loop to iterate over each game and calculate the form score for each team based on their performance in the last 5 games.
2. Step 2: Store the form scores in a data structure.
3. Step 3: Incorporate the form variable as a covariate into the extended Bradley-Terry model.
4. Step 4: Fit the model and evaluate its performance.

---

## Implementation Files

| File | Purpose |
|------|---------|
| **implement_rec_168.py** | Main implementation |
| **test_rec_168.py** | Test suite |
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

impl = ImplementIntegrateRecentFormAsACovariate(config=config)
```

---

## Performance Characteristics

**Estimated Time:** 32 hours

---

## Dependencies

**Prerequisites:**
- Implement Extended Bradley-Terry Model for Match Outcome Prediction
- Automate Data Collection and ETL Processes

**Enables:**
- Enhanced system capabilities
- Improved prediction accuracy
- Better maintainability

---

## Usage Examples

### Example 1: Basic Usage

```python
# Basic implementation
from implement_rec_168 import ImplementIntegrateRecentFormAsACovariate

impl = ImplementIntegrateRecentFormAsACovariate()
impl.setup()
results = impl.execute()
```

---

## Integration with Other Sub-Phases

This recommendation integrates with:
- Phase 5 components
- Cross-phase dependencies as specified

---

## Testing

```bash
# Run test suite
cd /Users/ryanranft/nba-simulator-aws/docs/phases/phase_5/5.126_integrate_recent_form_as_a_covariate
python test_rec_168.py -v
```

---

## Troubleshooting

**Common Issues:**
- See IMPLEMENTATION_GUIDE.md for detailed troubleshooting

---

## Related Documentation

- **[STATUS.md](STATUS.md)** - Implementation status
- **[RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md)** - Source recommendations
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Detailed guide
- **[Phase 5 Index](../PHASE_5_INDEX.md)** - Parent phase overview

---

## Navigation

**Return to:** [Phase 5: Machine Learning](../PHASE_5_INDEX.md)

---

**Last Updated:** October 19, 2025
**Maintained By:** NBA Simulator AWS Team
**Source:** Econometrics versus the Bookmakers An econometric approach to sports betting
