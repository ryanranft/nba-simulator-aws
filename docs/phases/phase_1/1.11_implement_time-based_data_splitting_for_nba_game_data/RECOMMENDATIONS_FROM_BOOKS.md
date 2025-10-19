# Book Recommendations - rec_127

**Recommendation:** Implement Time-Based Data Splitting for NBA Game Data
**Source Book:** building machine learning powered applications going from idea to product
**Priority:** CRITICAL
**Added:** 2025-10-19

---

## Source Information

**Book:** building machine learning powered applications going from idea to product
**Chapter:** Chapter 5
**Category:** Testing

---

## Recommendation Details

When creating training, validation, and test sets, use time-based data splitting to prevent data leakage. Specifically, ensure that the test set consists of data from a later time period than the training set.

---

## Technical Details

Use Python with scikit-learn or pandas to split the data chronologically, setting a cutoff date for training data and using data after that date for testing.

---

## Expected Impact

Accurate model evaluation and realistic performance metrics.

---

## Implementation Priority

**Priority Level:** CRITICAL
**Estimated Time:** 4 hours

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
