# Book Recommendations - rec_031

**Recommendation:** Implement an FTI Architecture for NBA Data Pipelines
**Source Book:** LLM Engineers Handbook
**Priority:** CRITICAL
**Added:** 2025-10-19

---

## Source Information

**Book:** LLM Engineers Handbook
**Chapter:** Chapter 1
**Category:** Architecture

---

## Recommendation Details

Design the NBA analytics system around a Feature/Training/Inference (FTI) pipeline architecture. This promotes modularity, scalability, and reusability of data engineering, model training, and inference components.

---

## Technical Details

Utilize separate pipelines for feature engineering, model training, and inference. Implement feature store for feature sharing and versioning, and model registry for model versioning and tracking.

---

## Expected Impact

Improved scalability, maintainability, and reproducibility of the NBA analytics system. Reduces training-serving skew.

---

## Implementation Priority

**Priority Level:** CRITICAL
**Estimated Time:** 40 hours

---

## Dependencies

**No dependencies identified.**

---

## Related Recommendations

- See Phase index for related recommendations in this category
- Check IMPLEMENTATION_GUIDE.md for integration details

---

**Generated:** October 19, 2025
**Source:** Book Analysis System
