#!/bin/bash
#
# GameNight Test Suite Runner
# Runs all tests with coverage reporting
#
set -e

echo "=========================================="
echo "  GameNight Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track overall status
TESTS_FAILED=0

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Change to project root
cd "${PROJECT_ROOT}"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

# Run Python unit tests
echo -e "${BLUE}Running Python Unit Tests...${NC}"
echo "------------------------------------------"
if pytest tests/unit -v --cov=app --cov-report=term-missing:skip-covered --cov-branch --tb=short -p no:warnings; then
    echo -e "${GREEN}✓ Python unit tests passed${NC}"
else
    echo -e "${RED}✗ Python unit tests failed${NC}"
    TESTS_FAILED=1
fi
echo ""

# Run Python integration tests
echo -e "${BLUE}Running Python Integration Tests...${NC}"
echo "------------------------------------------"
if pytest tests/integration -v --cov=app --cov-append --cov-report=term-missing:skip-covered --tb=short -p no:warnings; then
    echo -e "${GREEN}✓ Python integration tests passed${NC}"
else
    echo -e "${RED}✗ Python integration tests failed${NC}"
    TESTS_FAILED=1
fi
echo ""

# Run JavaScript unit tests
echo -e "${BLUE}Running JavaScript Unit Tests...${NC}"
echo "------------------------------------------"
if npm run test:unit; then
    echo -e "${GREEN}✓ JavaScript unit tests passed${NC}"
else
    echo -e "${RED}✗ JavaScript unit tests failed${NC}"
    TESTS_FAILED=1
fi
echo ""

# Run E2E tests
echo -e "${BLUE}Running End-to-End Tests...${NC}"
echo "------------------------------------------"
if pytest tests/e2e -v --tb=short; then
    echo -e "${GREEN}✓ E2E tests passed${NC}"
else
    echo -e "${RED}✗ E2E tests failed${NC}"
    TESTS_FAILED=1
fi
echo ""

# Final summary
echo "=========================================="
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}  ✅ ALL TESTS PASSED${NC}"
    echo "=========================================="
    echo ""
    echo "📊 Coverage Report: htmlcov/index.html"
    echo "📈 JavaScript Coverage: coverage/index.html"
else
    echo -e "${RED}  ❌ SOME TESTS FAILED${NC}"
    echo "=========================================="
    exit 1
fi

echo ""
