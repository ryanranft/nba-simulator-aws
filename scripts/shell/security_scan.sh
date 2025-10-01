#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     COMPREHENSIVE SECURITY SCAN - Git History & Files      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PART 1: GIT HISTORY SCAN (All Commits)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. AWS Access Keys (AKIA pattern)
echo -n "1. AWS Access Keys (AKIA[A-Z0-9]{16})............ "
COUNT=$(git log --all -p | grep -E "AKIA[A-Z0-9]{16}" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 2. AWS Secret Access Keys (40 char base64)
echo -n "2. AWS Secret Keys (40+ char secrets)........... "
COUNT=$(git log --all -p | grep -E "aws_secret_access_key.*[A-Za-z0-9/+=]{40}" | grep -v "\\*\\*\\*\\*" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 3. Private Keys
echo -n "3. Private SSH/RSA Keys.......................... "
COUNT=$(git log --all -p | grep -E "BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 4. GitHub Personal Access Tokens
echo -n "4. GitHub Tokens (ghp_, gho_, ghs_, ghr_)........ "
COUNT=$(git log --all -p | grep -E "gh[psor]_[A-Za-z0-9]{36}" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 5. Passwords in connection strings (excluding safe patterns)
echo -n "5. Passwords (postgresql://user:pass@host)....... "
COUNT=$(git log --all -p | grep -E "postgresql://[^:]+:[^@]{8,}@" | grep -v "PASSWORD\|\\*\\*\\*\\*\|\\[REDACTED\\]\|\${DB_PASSWORD}\|# Format:" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${YELLOW}⚠ WARN ($COUNT found - verify placeholders)${NC}"
fi

# 6. Private IP Addresses
echo -n "6. Private IPs (192.168.x.x, 10.x.x.x)........... "
COUNT=$(git log --all -p | grep -E "(192\.168\.|10\.)[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${YELLOW}⚠ WARN ($COUNT found - check if removed)${NC}"
fi

# 7. Credential backup paths
echo -n "7. Credential Paths (<credential-path>, aws_ranft)...... "
COUNT1=$(git log --all -p | grep -c "<credential-path>" | tr -d ' ')
COUNT2=$(git log --all -p | grep -c "aws_ranft" | tr -d ' ')
TOTAL=$((COUNT1 + COUNT2))
if [ "$TOTAL" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($TOTAL found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + TOTAL))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PART 2: CURRENT FILES SCAN (Working Directory)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 8. Check tracked files for AKIA
echo -n "8. Tracked Files - AWS Keys (AKIA)............... "
COUNT=$(git ls-files | xargs grep -E "AKIA[A-Z0-9]{16}" 2>/dev/null | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 9. Check tracked files for private keys
echo -n "9. Tracked Files - Private Keys.................. "
COUNT=$(git ls-files | xargs grep -E "BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY" 2>/dev/null | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 10. Check for .env files in tracked files
echo -n "10. Tracked Files - .env files................... "
COUNT=$(git ls-files | grep "\.env$" | grep -v "\.env\.example" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 11. Check for AWS credentials file
echo -n "11. Tracked Files - AWS credentials.............. "
COUNT=$(git ls-files | grep -E "(credentials|config)" | grep "\.aws" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
fi

# 12. Check for sensitive file patterns (excluding safe documentation examples)
echo -n "12. Tracked Files - Sensitive patterns........... "
COUNT=$(git ls-files | xargs grep -iE "password.*=.*[a-zA-Z0-9]{8,}" 2>/dev/null | grep -v "PASSWORD\|password_here\|your_password\|your_actual_password\|DB_PASSWORD\|\\.example" | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS (0 found)${NC}"
else
    echo -e "${YELLOW}⚠ WARN ($COUNT found - verify placeholders)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PART 3: SECURITY CONFIGURATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 13. Check .gitignore
echo -n "13. .gitignore exists and has .env............... "
if [ -f .gitignore ] && grep -q "\.env$" .gitignore; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 14. Check pre-commit hook
echo -n "14. Pre-commit hook exists....................... "
if [ -f .git/hooks/pre-commit ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${YELLOW}⚠ WARN (not found)${NC}"
fi

# 15. Check pre-push hook
echo -n "15. Pre-push hook exists......................... "
if [ -f .git/hooks/pre-push ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${YELLOW}⚠ WARN (not found)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FINAL RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ SECURITY SCAN PASSED - NO CRITICAL ISSUES FOUND   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "✅ Your repository is SECURE and ready to commit/push!"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SECURITY SCAN FAILED - $ISSUES_FOUND ISSUES FOUND         ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "❌ DO NOT COMMIT until issues are resolved!"
    exit 1
fi
