## 🧪 Testing Workflows

**Follow test-driven development approach for all code**

### Before Writing Code
1. **Write test cases first** (if applicable)
   ```bash
   # Create test file
   touch tests/test_<module_name>.py
   ```
2. **Create test fixtures**
   - Sample data files
   - Mock AWS responses
   - Expected outputs
3. **Define success criteria**
   - What should pass?
   - What should fail?
   - Edge cases to cover

### While Writing Code
1. **Run tests frequently** (after each function/class)
   ```bash
   pytest tests/test_<module_name>.py -v
   ```
2. **Test-driven development cycle:**
   - Write failing test → Write code → Test passes → Refactor → Repeat
3. **Check coverage** (aim for >80%)
   ```bash
   pytest --cov=scripts tests/
   ```

### Before Committing Code
1. **Run ALL tests**
   ```bash
   pytest tests/ -v
   ```
2. **Check for test failures**
   - Fix all failures before commit
   - Document any expected failures
3. **Verify code coverage**
   ```bash
   pytest --cov=scripts --cov-report=html tests/
   ```
4. **Review test output** with user before commit

### Before AWS Deployment (Integration Testing)
1. **Run integration tests with sample data**
   ```bash
   python scripts/test_integration.py
   ```
2. **Verify AWS connectivity**
   - S3 bucket access
   - RDS connection (if applicable)
   - Glue job submission (if applicable)
3. **Manual validation checklist:**
   - ✅ Sample data processed correctly
   - ✅ Output format matches expectations
   - ✅ Error handling works (test with bad data)
   - ✅ Logging captures all operations
   - ✅ Performance acceptable (timing checks)

**See `docs/TESTING.md` for complete testing procedures and examples**

---

