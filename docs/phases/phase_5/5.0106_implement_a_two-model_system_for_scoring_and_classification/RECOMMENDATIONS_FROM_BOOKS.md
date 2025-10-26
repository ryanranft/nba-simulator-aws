# Book Recommendations - rec_141

**Recommendation:** Implement a Two-Model System for Scoring and Classification
**Source Book:** building machine learning powered applications going from idea to product
**Priority:** IMPORTANT
**Added:** 2025-10-19

---

## Source Information

**Book:** building machine learning powered applications going from idea to product
**Chapter:** Chapter 2
**Category:** Architecture

---

## Recommendation Details

To allow fine-tuning of system decisions, separate the system in two parts: a model dedicated to generating a score and a distinct system for translating scores to actions (e.g. reject/approve, surface/don't surface). This allows experimentation with both parts independently.

---

## Technical Details

Run the scoring model as a service. Create the system action layer as a separate component that queries scores from the scoring service and implements business rules.

---

## Expected Impact

More flexibility to run and assess different business decisions

---

## Implementation Priority

**Priority Level:** IMPORTANT
**Estimated Time:** 16 hours

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
