# 5.118: Incorporate Team Salaries as a Covariate in the Model

**Sub-Phase:** 5.118 (ML)
**Parent Phase:** [Phase 5: Machine Learning](../PHASE_5_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** 🟡 IMPORTANT
**Implementation ID:** rec_157

---

## Overview

Integrate NBA team salary data into the extended Bradley-Terry model as a covariate.  Explore both linear and logarithmic forms of salary data to determine the best fit.  Handle potential data availability issues by projecting salaries based on historical trends.

**Key Capabilities:**
- Integration with data pipeline for salary data retrieval, data transformation (linear vs
- log), model re-fitting with salary covariate, A/B testing of model performance with and without salary.

**Impact:**
Potentially improve model accuracy by incorporating a key factor influencing team performance. The book suggests a high correlation between salaries and performance in football.

---

## Quick Start

```python
from implement_rec_157 import ImplementIncorporateTeamSalariesAsACovariateInTheModel

# Initialize implementation
impl = ImplementIncorporateTeamSalariesAsACovariateInTheModel()
impl.setup()

# Execute implementation
results = impl.execute()

print(f"Implementation complete: {results}")
```

---

## Architecture

### Implementation Steps

1. Step 1: Create a data pipeline to ingest NBA team salary data.
2. Step 2: Transform salary data into both linear and logarithmic forms.
3. Step 3: Incorporate the salary data as a covariate into the extended Bradley-Terry model.
4. Step 4: Fit the model with both linear and logarithmic salary data.
5. Step 5: Compare the performance of the models using historical data (backtesting) and select the best performing form.
6. Step 6: If current salary data is unavailable, implement a projection based on historical salary trends and inflation.

---

## Implementation Files

| File | Purpose |
|------|---------|
| **implement_rec_157.py** | Main implementation |
| **test_rec_157.py** | Test suite |
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

impl = ImplementIncorporateTeamSalariesAsACovariateInTheModel(config=config)
```

---

## Performance Characteristics

**Estimated Time:** 40 hours

---

## Dependencies

**Prerequisites:**
- Implement Extended Bradley-Terry Model for Match Outcome Prediction

**Enables:**
- Enhanced system capabilities
- Improved prediction accuracy
- Better maintainability

---

## Usage Examples

### Example 1: Basic Usage

```python
# Basic implementation
from implement_rec_157 import ImplementIncorporateTeamSalariesAsACovariateInTheModel

impl = ImplementIncorporateTeamSalariesAsACovariateInTheModel()
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
cd /Users/ryanranft/nba-simulator-aws/docs/phases/phase_5/5.0118_incorporate_team_salaries_as_a_covariate_in_the_model
python test_rec_157.py -v
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
