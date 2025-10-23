#!/bin/bash
# Test Reconciliation Engine - ADCE Phase 2A MVP
# Quick validation that all components are installed and working

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Testing Reconciliation Engine - Phase 2A"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

test_file() {
    local file=$1
    local name=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $name exists"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $name missing: $file"
        ((failed++))
    fi
}

test_executable() {
    local file=$1
    local name=$2

    if [ -x "$file" ]; then
        echo -e "${GREEN}✓${NC} $name is executable"
        ((passed++))
    else
        echo -e "${YELLOW}⚠${NC} $name not executable: $file"
    fi
}

test_python_syntax() {
    local file=$1
    local name=$2

    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name has valid Python syntax"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $name has syntax errors"
        ((failed++))
    fi
}

test_yaml_syntax() {
    local file=$1
    local name=$2

    if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name has valid YAML syntax"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $name has YAML syntax errors"
        ((failed++))
    fi
}

echo "1. Testing Configuration Files"
echo "--------------------------------------"
test_file "inventory/data_inventory.yaml" "Expected coverage schema"
test_yaml_syntax "inventory/data_inventory.yaml" "Expected coverage schema"
test_file "config/reconciliation_config.yaml" "Reconciliation config"
test_yaml_syntax "config/reconciliation_config.yaml" "Reconciliation config"
echo ""

echo "2. Testing Python Scripts"
echo "--------------------------------------"
test_file "scripts/reconciliation/scan_s3_inventory.py" "S3 Scanner"
test_executable "scripts/reconciliation/scan_s3_inventory.py" "S3 Scanner"
test_python_syntax "scripts/reconciliation/scan_s3_inventory.py" "S3 Scanner"

test_file "scripts/reconciliation/analyze_coverage.py" "Coverage Analyzer"
test_executable "scripts/reconciliation/analyze_coverage.py" "Coverage Analyzer"
test_python_syntax "scripts/reconciliation/analyze_coverage.py" "Coverage Analyzer"

test_file "scripts/reconciliation/detect_data_gaps.py" "Gap Detector"
test_executable "scripts/reconciliation/detect_data_gaps.py" "Gap Detector"
test_python_syntax "scripts/reconciliation/detect_data_gaps.py" "Gap Detector"

test_file "scripts/reconciliation/generate_task_queue.py" "Task Generator"
test_executable "scripts/reconciliation/generate_task_queue.py" "Task Generator"
test_python_syntax "scripts/reconciliation/generate_task_queue.py" "Task Generator"

test_file "scripts/reconciliation/run_reconciliation.py" "Pipeline Runner"
test_executable "scripts/reconciliation/run_reconciliation.py" "Pipeline Runner"
test_python_syntax "scripts/reconciliation/run_reconciliation.py" "Pipeline Runner"
echo ""

echo "3. Testing Directory Structure"
echo "--------------------------------------"
test_file "scripts/reconciliation/README.md" "Reconciliation README"

if [ -d "inventory/cache" ]; then
    echo -e "${GREEN}✓${NC} Cache directory exists"
    ((passed++))
else
    echo -e "${YELLOW}⚠${NC} Cache directory will be created on first run"
fi
echo ""

echo "4. Testing Dependencies"
echo "--------------------------------------"
# Test Python is available
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 available"
    ((passed++))
else
    echo -e "${RED}✗${NC} Python 3 not found"
    ((failed++))
fi

# Test boto3 (AWS SDK)
if python3 -c "import boto3" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} boto3 (AWS SDK) installed"
    ((passed++))
else
    echo -e "${RED}✗${NC} boto3 not installed (required for S3 access)"
    ((failed++))
fi

# Test PyYAML
if python3 -c "import yaml" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PyYAML installed"
    ((passed++))
else
    echo -e "${RED}✗${NC} PyYAML not installed"
    ((failed++))
fi
echo ""

echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $passed"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $failed"
else
    echo -e "${GREEN}Failed:${NC} 0"
fi
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run reconciliation: python scripts/reconciliation/run_reconciliation.py --dry-run"
    echo "  2. Review README: scripts/reconciliation/README.md"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Please fix the errors above before proceeding"
    exit 1
fi

