# Book Recommendations - rec_045

**Recommendation:** Use Qdrant as a Logical Feature Store
**Source Book:** LLM Engineers Handbook
**Priority:** IMPORTANT
**Added:** 2025-10-19

---

## Source Information

**Book:** LLM Engineers Handbook
**Chapter:** Chapter 4
**Category:** Data Processing

---

## Recommendation Details

Implement a logical feature store using Qdrant and ZenML artifacts. This provides a versioned and reusable training dataset and online access for inference.

---

## Technical Details

Store cleaned data in Qdrant without embeddings. Use ZenML artifacts to wrap the data and add metadata. Implement a data discovery interface to connect with the feature store.

---

## Expected Impact

Versioned and reusable training dataset, online access for inference, and easy feature discovery.

---

## Implementation Priority

**Priority Level:** IMPORTANT
**Estimated Time:** 16 hours

---

## Dependencies

**Required Prerequisites:**

- Implement a RAG Feature Pipeline


---

## Related Recommendations

- See Phase index for related recommendations in this category
- Check IMPLEMENTATION_GUIDE.md for integration details

---

**Generated:** October 19, 2025
**Source:** Book Analysis System
