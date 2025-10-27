# Test Fixtures

**Purpose:** Shared test data and mock objects

**Contents:**
- Sample NBA game data (JSON files)
- Mock AWS responses
- Test database schemas
- Reusable test utilities

**Usage:**
```python
from tests.fixtures import sample_data

def test_something():
    game_data = sample_data.load_sample_game()
    assert game_data["game_id"] == "401584876"
```

**Guidelines:**
- Keep fixtures small and focused
- Use realistic NBA data
- Document data sources
- Version control fixtures
