# Makefile for api-demo WAF testing application

.PHONY: help install test test-ci test-unit test-integration test-vulnerability test-smoke test-coverage test-parallel test-all clean run run-vulnerable run-secure

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

UV ?= uv

# Default target
help:
	@echo "$(BLUE)Chimera - WAF Testing Application$(NC)"
	@echo ""
	@echo "Available targets:"
	@echo "  $(GREEN)install$(NC)           - Install dependencies"
	@echo "  $(GREEN)test$(NC)              - Run all tests"
	@echo "  $(GREEN)test-unit$(NC)         - Run unit tests with coverage"
	@echo "  $(GREEN)test-integration$(NC)  - Run integration tests"
	@echo "  $(GREEN)test-vulnerability$(NC) - Run vulnerability tests"
	@echo "  $(GREEN)test-smoke$(NC)        - Run smoke tests"
	@echo "  $(GREEN)test-coverage$(NC)     - Check code coverage"
	@echo "  $(GREEN)test-parallel$(NC)     - Run tests in parallel"
	@echo "  $(GREEN)test-report$(NC)       - Generate HTML test report"
	@echo "  $(GREEN)run$(NC)               - Run application (vulnerable mode)"
	@echo "  $(GREEN)run-vulnerable$(NC)    - Run in vulnerable mode (DEMO_MODE=full)"
	@echo "  $(GREEN)run-secure$(NC)        - Run in secure mode (DEMO_MODE=strict)"
	@echo "  $(GREEN)clean$(NC)             - Clean up generated files"
	@echo "  $(GREEN)lint$(NC)              - Run code linters"
	@echo "  $(GREEN)format$(NC)            - Format code with black"
	@echo ""
	@echo "Examples:"
	@echo "  make install       # Install dependencies"
	@echo "  make test          # Run all tests"
	@echo "  make run           # Start the application"

# Install dependencies
install:
	@echo "$(BLUE)Installing dependencies with uv...$(NC)"
	$(UV) sync --extra dev --frozen
	$(UV) pip install -r ../tests/requirements-test.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

# Run all tests
test: test-all

# CI test target (unit tests with coverage, fail-fast)
test-ci:
	@echo "$(BLUE)Running CI tests...$(NC)"
	@export DEMO_MODE=full && \
	$(UV) run pytest tests/unit -v --cov=app --cov-report=term-missing -x --maxfail=5

# Run unit tests with coverage
test-unit:
	@echo "$(BLUE)Running unit tests...$(NC)"
	@export DEMO_MODE=full && \
	$(UV) run pytest tests/unit -v --cov=app --cov-report=term-missing --cov-report=html

# Run integration tests
test-integration:
	@echo "$(BLUE)Running integration tests...$(NC)"
	@export DEMO_MODE=full && \
	$(UV) run pytest tests/integration -v -m integration

# Run vulnerability tests
test-vulnerability:
	@echo "$(BLUE)Running vulnerability tests...$(NC)"
	@export DEMO_MODE=full && \
	$(UV) run pytest tests -v -m vulnerability

# Run smoke tests
test-smoke:
	@echo "$(BLUE)Running smoke tests...$(NC)"
	@$(UV) run pytest tests/smoke -v -m smoke --tb=short

# Check code coverage
test-coverage:
	@echo "$(BLUE)Checking code coverage...$(NC)"
	@$(UV) run pytest tests/unit --cov=app --cov-report=term --cov-fail-under=80

# Run tests in parallel
test-parallel:
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	@$(UV) run pytest tests -n auto -v

# Generate test report
test-report:
	@echo "$(BLUE)Generating test report...$(NC)"
	@mkdir -p reports
	@$(UV) run pytest tests --html=reports/test_report.html --self-contained-html
	@echo "$(GREEN)✓ Report generated: reports/test_report.html$(NC)"

# Run all test suites
test-all:
	@echo "$(BLUE)Running complete test suite...$(NC)"
	@./run_tests.sh all

# Clean up generated files
clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf reports/ 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Run application in vulnerable mode (default)
run: run-vulnerable

# Run application in vulnerable mode
run-vulnerable:
	@echo "$(RED)⚠️  Starting in VULNERABLE mode (DEMO_MODE=full)$(NC)"
	@echo "$(YELLOW)This mode has intentional security vulnerabilities for testing!$(NC)"
	@export DEMO_MODE=full && \
	export FLASK_ENV=development && \
	$(UV) run gunicorn 'app:create_app()' --config gunicorn.conf.py

# Run application in secure mode
run-secure:
	@echo "$(GREEN)Starting in SECURE mode (DEMO_MODE=strict)$(NC)"
	@export DEMO_MODE=strict && \
	export FLASK_ENV=production && \
	$(UV) run gunicorn 'app:create_app()' --config gunicorn.conf.py

# Run code linters
lint:
	@echo "$(BLUE)Running linters...$(NC)"
	@flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503 || true
	@pylint app/ tests/ --max-line-length=120 --disable=C0114,C0115,C0116 || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

# Format code with black
format:
	@echo "$(BLUE)Formatting code...$(NC)"
	@black app/ tests/ --line-length=120
	@echo "$(GREEN)✓ Formatting complete$(NC)"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify a test file$(NC)"; \
		echo "Usage: make test-file FILE=tests/unit/test_auth_routes.py"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running test: $(FILE)$(NC)"
	@pytest $(FILE) -v

# Quick test for CI/CD
test-quick:
	@echo "$(BLUE)Running quick tests...$(NC)"
	@pytest tests/unit -v --tb=short -x --maxfail=5

# Test with different demo modes
test-modes:
	@echo "$(BLUE)Testing with DEMO_MODE=strict...$(NC)"
	@export DEMO_MODE=strict && pytest tests/unit -v -k "not vulnerability"
	@echo ""
	@echo "$(BLUE)Testing with DEMO_MODE=full...$(NC)"
	@export DEMO_MODE=full && pytest tests/unit -v -k "vulnerability"
