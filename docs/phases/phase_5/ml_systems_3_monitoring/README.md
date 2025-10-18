# ML Monitoring System

**Recommendation ID:** ml_systems_3
**Status:** ✅ **COMPLETE** (Infrastructure integrated in `/scripts/monitoring/`)
**Integration Type:** Infrastructure / MLOps

---

## Overview

Unified monitoring dashboard for NBA ML systems. Integrates MLflow (ml_systems_1) and drift detection (ml_systems_2) metrics into real-time visualization.

**Key Capabilities:**
- Model performance tracking over time
- Drift detection visualization  
- Feature importance monitoring
- Prediction distribution analysis
- Alert system integration

---

## Quick Start

```bash
# Launch monitoring dashboard
python scripts/monitoring/unified_monitoring_dashboard.py --refresh 30

# Access at: http://localhost:8050
```

---

## Integration Points

**ml_systems_1 (MLflow):**
- Display model versions and stages
- Show experiment comparison
- Track model promotion history

**ml_systems_2 (Drift Detection):**
- Visualize drift metrics (PSI, KS, Chi²)
- Alert when thresholds exceeded
- Show feature-level drift over time

**rec_11 (Feature Engineering):**
- Monitor 80+ engineered features
- Track feature importance changes
- Detect unstable features

---

## Implementation

Monitoring code integrated in:
- `/scripts/monitoring/unified_monitoring_dashboard.py`
- `/scripts/monitoring/scraper_health_monitor.py`
- `/scripts/monitoring/data_quality_monitor.py`

---

## Related Documentation

- [STATUS.md](STATUS.md) - Implementation status
- [RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md) - Book sources

---

**Last Updated:** October 18, 2025
**Maintained By:** NBA Simulator AWS Team
