#!/bin/bash
# Test runner script for Gym Dorian API
# This script provides convenient commands for running tests

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}================================${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-"all"}

case $COMMAND in
    "all")
        print_header "Running All Tests"
        pytest -v
        ;;
    
    "unit")
        print_header "Running Unit Tests"
        pytest -v -m unit
        ;;
    
    "integration")
        print_header "Running Integration Tests"
        pytest -v -m integration
        ;;
    
    "fast")
        print_header "Running Fast Tests (excluding slow)"
        pytest -v -m "not slow"
        ;;
    
    "coverage")
        print_header "Running Tests with Coverage Report"
        pytest --cov=app --cov-report=html --cov-report=term-missing
        print_info "Coverage report generated in htmlcov/index.html"
        ;;
    
    "smoke")
        print_header "Running Smoke Tests"
        pytest -v -m smoke --tb=short
        ;;
    
    "verbose")
        print_header "Running All Tests (Extra Verbose)"
        pytest -vv -l
        ;;
    
    "failed")
        print_header "Re-running Failed Tests"
        pytest --lf -v
        ;;
    
    "watch")
        print_header "Running Tests in Watch Mode"
        if command -v pytest-watch &> /dev/null; then
            pytest-watch -- -v
        else
            print_error "pytest-watch not installed. Run: pip install pytest-watch"
            exit 1
        fi
        ;;
    
    "health")
        print_header "Running Health Check Tests"
        pytest -v app/tests/integration/test_health.py
        ;;
    
    "models")
        print_header "Running Model Tests"
        pytest -v app/tests/integration/test_exercise_model.py app/tests/integration/test_workout_models.py
        ;;
    
    "help"|"-h"|"--help")
        echo "Gym Dorian API Test Runner"
        echo ""
        echo "Usage: ./run_tests.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  all           Run all tests (default)"
        echo "  unit          Run only unit tests"
        echo "  integration   Run only integration tests"
        echo "  fast          Run fast tests (exclude slow tests)"
        echo "  coverage      Run tests with coverage report"
        echo "  smoke         Run smoke tests for quick validation"
        echo "  verbose       Run tests with extra verbose output"
        echo "  failed        Re-run only failed tests"
        echo "  watch         Run tests in watch mode (requires pytest-watch)"
        echo "  health        Run health check tests only"
        echo "  models        Run model tests only"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh all"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh integration"
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Print summary if tests passed
if [ $? -eq 0 ]; then
    echo ""
    print_info "Tests completed successfully! ✓"
fi
