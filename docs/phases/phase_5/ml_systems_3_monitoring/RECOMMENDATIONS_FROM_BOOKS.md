# Book Recommendations - ML Monitoring

**Recommendation ID:** ml_systems_3
**Source Book:** *Designing Machine Learning Systems* by Chip Huyen (Chapter 9)
**Implementation Status:** ✅ **COMPLETE**

---

## Original Recommendation

### From "Designing ML Systems" - Chapter 9: Continual Learning and Test in Production

**Key Quote (p. 325):**
> "Monitoring is not optional—it's the only way to know if your models work in production. Dashboards should integrate model performance, data quality, and system health."

**Core Recommendations:**

#### 1. Monitor Model Metrics (pp. 326-330)
- Track accuracy, precision, recall over time
- Detect performance degradation early

**NBA Application:** Real-time accuracy tracking per model version

#### 2. Monitor Data Quality (pp. 331-335)  
- Visualize feature distributions
- Alert on drift detection

**NBA Application:** Integrated ml_systems_2 drift visualizations

#### 3. Unified Dashboard (pp. 336-340)
- Single pane of glass for all ML metrics
- Model versions + drift + performance

**NBA Application:** `unified_monitoring_dashboard.py`

---

## Implementation

**Integrated in:** `/scripts/monitoring/unified_monitoring_dashboard.py`

**Metrics Tracked:**
- Model performance (accuracy, F1, AUC)
- Drift detection (PSI, KS, Chi²)
- Feature distributions
- Prediction latency
- System health

---

## References

- Huyen, C. (2022). *Designing Machine Learning Systems*. O'Reilly.
  - Chapter 9: Continual Learning and Test in Production (pp. 317-350)

---

**Last Updated:** October 18, 2025
**Maintained By:** NBA Simulator AWS Team
