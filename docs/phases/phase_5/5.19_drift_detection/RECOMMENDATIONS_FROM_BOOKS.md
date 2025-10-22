# Book Recommendations - Data Drift Detection

**Recommendation ID:** ml_systems_2
**Source Book:** *Designing Machine Learning Systems* by Chip Huyen (Chapter 8)
**MCP Analysis:** October 2025
**Implementation Status:** ✅ **COMPLETE**

---

## Original Recommendation

### From "Designing ML Systems" - Chapter 8: Data Distribution Shifts and Monitoring

**Key Quote (p. 285):**
> "Data drift is inevitable in production. Without monitoring, models silently degrade. Statistical tests like PSI, KS, and Chi-squared detect distribution shifts before they harm business metrics."

**Core Recommendations:**

#### 1. Monitor Input Distributions (pp. 286-290)
- Track feature distributions over time
- Compare production data to training data
- Alert when distributions diverge significantly

**NBA Application:** Monitor all 80 features from rec_11

#### 2. Use Multiple Methods (pp. 291-295)
- PSI for overall shift
- KS test for numerical features
- Chi-squared for categorical features

**NBA Application:** 5 complementary statistical methods

#### 3. Set Appropriate Thresholds (pp. 296-298)
- PSI ≥ 0.2 = significant drift
- KS stat ≥ 0.1 = distribution change
- Chi² p-value < 0.05 = category shift

**NBA Application:** Configurable thresholds per method

#### 4. Trigger Retraining (pp. 299-302)
- When drift detected → retrain model
- Register new version with MLflow
- Deploy and monitor new model

**NBA Application:** Integration with ml_systems_1

---

## Implementation Synthesis

**Statistical Rigor:**
- Huyen emphasizes using proven statistical methods
- **Implementation:** 5 standard tests from literature

**Automated Monitoring:**
- Huyen recommends continuous monitoring
- **Implementation:** Integrated with MLflow for tracking

**Actionable Alerts:**
- Huyen warns against alert fatigue
- **Implementation:** Tunable thresholds, feature-level detail

---

## References

- Huyen, C. (2022). *Designing Machine Learning Systems*. O'Reilly.
  - Chapter 8: Data Distribution Shifts (pp. 281-315)

---

**Last Updated:** October 18, 2025
**Maintained By:** NBA Simulator AWS Team
