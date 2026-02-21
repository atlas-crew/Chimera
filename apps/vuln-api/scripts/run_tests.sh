#!/bin/bash
# Test runner for api-demo WAF testing application

set -eo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}uv is not installed. Install it from https://github.com/astral-sh/uv before running tests.${NC}"
    exit 1
fi

# Test configuration
TEST_DIR="tests"
COVERAGE_THRESHOLD=80
DEMO_MODE=${DEMO_MODE:-"full"}

# Print colored output
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${MAGENTA}ℹ $1${NC}"
}

# Function to run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"

    export DEMO_MODE=$DEMO_MODE

    if uv run pytest tests/unit -v --cov=app --cov-report=term-missing --cov-report=html; then
        print_success "Unit tests passed!"
        return 0
    else
        print_error "Unit tests failed!"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"

    export DEMO_MODE=$DEMO_MODE

    if uv run pytest tests/integration -v -m integration; then
        print_success "Integration tests passed!"
        return 0
    else
        print_error "Integration tests failed!"
        return 1
    fi
}

# Function to run vulnerability tests
run_vulnerability_tests() {
    print_header "Running Vulnerability Tests (DEMO_MODE=full)"

    export DEMO_MODE=full

    if uv run pytest tests -v -m vulnerability; then
        print_success "Vulnerability tests passed!"
        return 0
    else
        print_error "Vulnerability tests failed!"
        return 1
    fi
}

# Function to run smoke tests
run_smoke_tests() {
    print_header "Running Smoke Tests"

    if uv run pytest tests/smoke -v -m smoke --tb=short; then
        print_success "Smoke tests passed!"
        return 0
    else
        print_error "Smoke tests failed!"
        return 1
    fi
}

# Function to check coverage
check_coverage() {
    print_header "Checking Code Coverage"

    coverage_output=$(uv run pytest tests/unit --cov=app --cov-report=term 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')

    if [ ! -z "$coverage_output" ]; then
        if [ $(echo "$coverage_output >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ]; then
            print_success "Code coverage: ${coverage_output}% (threshold: ${COVERAGE_THRESHOLD}%)"
            return 0
        else
            print_warning "Code coverage: ${coverage_output}% is below threshold: ${COVERAGE_THRESHOLD}%"
            return 1
        fi
    else
        print_warning "Could not determine code coverage"
        return 1
    fi
}

# Function to run specific test file
run_specific_test() {
    local test_file=$1
    print_header "Running Test: $test_file"

    if uv run pytest "$test_file" -v; then
        print_success "Test passed: $test_file"
        return 0
    else
        print_error "Test failed: $test_file"
        return 1
    fi
}

# Function to run tests in parallel
run_parallel_tests() {
    print_header "Running Tests in Parallel"

    if uv run pytest tests -n auto -v; then
        print_success "Parallel tests passed!"
        return 0
    else
        print_error "Parallel tests failed!"
        return 1
    fi
}

# Function to generate test report
generate_report() {
    print_header "Generating Test Report"

    uv run pytest tests --html=reports/test_report.html --self-contained-html

    if [ -f "reports/test_report.html" ]; then
        print_success "Test report generated: reports/test_report.html"
        print_success "Coverage report generated: htmlcov/index.html"
    else
        print_warning "Could not generate test report"
    fi
}

# Parse command line arguments
case "${1:-all}" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    vulnerability)
        run_vulnerability_tests
        ;;
    smoke)
        run_smoke_tests
        ;;
    coverage)
        check_coverage
        ;;
    parallel)
        run_parallel_tests
        ;;
    report)
        generate_report
        ;;
    specific)
        if [ -z "$2" ]; then
            print_error "Please specify a test file"
            exit 1
        fi
        run_specific_test "$2"
        ;;
    all)
        print_header "Running Complete Test Suite"

        TOTAL_TESTS=0
        PASSED_TESTS=0

        # Run each test type
        for test_type in smoke unit integration vulnerability; do
            echo ""
            if run_${test_type}_tests; then
                ((PASSED_TESTS++))
            fi
            ((TOTAL_TESTS++))
        done

        echo ""
        check_coverage

        echo ""
        print_header "Test Summary"
        echo -e "Tests Run: $TOTAL_TESTS"
        echo -e "Tests Passed: $PASSED_TESTS"

        if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
            print_success "All test suites passed!"
            generate_report
            exit 0
        else
            print_error "Some test suites failed"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [unit|integration|vulnerability|smoke|coverage|parallel|report|all|specific <test_file>]"
        echo ""
        echo "Options:"
        echo "  unit          - Run unit tests with coverage"
        echo "  integration   - Run integration tests"
        echo "  vulnerability - Run vulnerability tests (DEMO_MODE=full)"
        echo "  smoke         - Run quick smoke tests"
        echo "  coverage      - Check code coverage"
        echo "  parallel      - Run tests in parallel"
        echo "  report        - Generate HTML test report"
        echo "  specific      - Run a specific test file"
        echo "  all           - Run all test suites (default)"
        echo ""
        echo "Environment Variables:"
        echo "  DEMO_MODE     - Set demo mode (full|strict), default: full"
        echo ""
        echo "Examples:"
        echo "  $0 unit                          # Run unit tests"
        echo "  $0 specific tests/unit/test_auth_routes.py  # Run specific test"
        echo "  DEMO_MODE=strict $0 all          # Run all tests in strict mode"
        exit 1
        ;;
esac
