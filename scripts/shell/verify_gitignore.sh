#!/bin/bash

# verify_gitignore.sh
# Verify that sensitive file patterns are properly excluded in .gitignore

echo "🔍 Verifying .gitignore security settings..."

GITIGNORE_FILE=".gitignore"
EXIT_CODE=0

# Required patterns in .gitignore
REQUIRED_PATTERNS=(
    ".env$"
    "*.key"
    "*.pem"
    "credentials.yaml"
    "*credentials*"
)

if [ ! -f "$GITIGNORE_FILE" ]; then
    echo "❌ .gitignore file not found!"
    exit 1
fi

echo ""
echo "Checking for required security patterns:"
echo ""

for pattern in "${REQUIRED_PATTERNS[@]}"; do
    if grep -q "$pattern" "$GITIGNORE_FILE"; then
        echo "  ✅ $pattern"
    else
        echo "  ❌ MISSING: $pattern"
        EXIT_CODE=1
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All security patterns present in .gitignore"
else
    echo ""
    echo "❌ Some security patterns are missing from .gitignore"
    echo "   Add missing patterns to prevent accidental credential commits"
fi

exit $EXIT_CODE
