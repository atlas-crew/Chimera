# Chimera Test Suite

Comprehensive testing framework for the WAF testing application with 200+ tests covering functionality, vulnerabilities, and integrations.

## 📊 Test Coverage Summary

- **Total Tests**: 267
- **Overall Coverage**: 94%
- **Test Execution Time**: ~12 seconds

### Coverage by Module
| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| Auth | 31 | 97% | ✅ |
| Banking | 27 | 95% | ✅ |
| Healthcare | 49 | 93% | ✅ |
| Admin | 75 | 92% | ✅ |
| Utils | 85 | 96% | ✅ |

## 🚀 Quick Start

### Run All Tests
```bash
# From api-demo directory
make test

# Or directly with pytest
pytest
```

### Quick Sanity Check
```bash
# Run fast tests only (< 5 seconds)
make test-quick

# Or use the script
./run_tests.sh --quick
```

### With Coverage Report
```bash
# Generate HTML coverage report
make test-coverage

# View report
open htmlcov/index.html
```

## 📁 Test Structure

```
tests/
├── unit/                           # Component tests
│   ├── test_sample.py             # Example patterns (5 tests)
│   ├── test_dal.py                # Data layer (25 tests)
│   ├── test_validators.py         # Input validation (20 tests)
│   ├── test_responses.py          # Response formatting (18 tests)
│   ├── test_auth_helpers.py       # Auth utilities (22 tests)
│   ├── test_auth_routes.py        # Auth endpoints (31 tests)
│   ├── test_banking_routes.py     # Banking endpoints (27 tests)
│   ├── test_healthcare_routes.py  # Healthcare endpoints (49 tests)
│   └── test_admin_routes.py       # Admin endpoints (75 tests)
├── integration/                    # End-to-end tests
│   ├── test_auth_flow.py         # Complete auth workflows
│   ├── test_transaction_flow.py  # Banking transactions
│   └── test_admin_operations.py  # Admin scenarios
├── vulnerability/                  # Security validation
│   ├── test_sql_injection.py     # SQL injection patterns
│   ├── test_xss.py               # XSS validation
│   ├── test_command_injection.py # Command injection
│   └── test_auth_bypass.py       # Authentication bypass
├── conftest.py                    # Pytest configuration
├── pytest.ini                     # Pytest settings
├── run_tests.sh                   # Test runner script
├── Makefile                       # Test automation
└── README.md                      # This file
```

## 🧪 Test Categories

### Unit Tests
Test individual components in isolation:
- Data Access Layer operations
- Input validators
- Response formatters
- Authentication helpers
- Individual route handlers

### Integration Tests
Test complete workflows:
- User registration → login → action → logout
- Banking transaction flows
- Healthcare record management
- Admin operations

### Vulnerability Tests
Validate intentional security flaws:
- SQL injection detection
- XSS payload handling
- Command injection attempts
- Authentication bypasses
- Path traversal attacks

## 🎯 Running Specific Tests

### By Module
```bash
# Auth module only
pytest tests/unit/test_auth_routes.py -v

# Banking module
pytest tests/unit/test_banking_routes.py -v

# Healthcare module
pytest tests/unit/test_healthcare_routes.py -v

# Admin module
pytest tests/unit/test_admin_routes.py -v
```

### By Category
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Vulnerability tests
pytest tests/vulnerability/ -v
```

### By Marker
```bash
# Fast tests only
pytest -m "not slow"

# Security tests
pytest -m security

# Critical tests
pytest -m critical
```

### Individual Test
```bash
# Run single test
pytest tests/unit/test_auth_routes.py::test_sql_injection_login -v

# Run with print output
pytest tests/unit/test_auth_routes.py::test_sql_injection_login -v -s
```

## 🔍 Test Examples

### Testing Vulnerabilities
```python
def test_sql_injection_login(client):
    """Test SQL injection vulnerability in login"""
    response = client.post('/api/v1/auth/login',
        json={
            'username': "admin' OR '1'='1",
            'password': 'any'
        })
    assert response.status_code == 200
    assert response.json['success'] == True
```

### Testing Business Logic
```python
def test_insufficient_balance_transfer(client):
    """Test transfer with insufficient balance"""
    response = client.post('/api/v1/banking/transfer',
        json={
            'from_account': 'ACC001',
            'to_account': 'ACC002',
            'amount': 1000000
        })
    assert response.status_code == 400
    assert 'insufficient' in response.json['error'].lower()
```

### Testing Data Validation
```python
def test_invalid_email_format(client):
    """Test email validation"""
    response = client.post('/api/v1/auth/register',
        json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'password123'
        })
    assert response.status_code == 400
    assert 'email' in response.json['errors']
```

## 📈 Coverage Reports

### Generate Coverage Report
```bash
# Terminal report
pytest --cov=app --cov-report=term

# HTML report
pytest --cov=app --cov-report=html

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Requirements
- Minimum overall: 90%
- New code: 95%
- Critical paths: 100%

## 🛠️ Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    security: security-related tests
    critical: critical path tests
```

### conftest.py
Provides shared fixtures:
- `client` - Flask test client
- `auth_headers` - Authentication headers
- `sample_data` - Test data fixtures
- `mock_services` - Service mocks

## 🚦 Continuous Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: make test-coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 🔧 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure in api-demo directory
cd api-demo
# Install test dependencies
pip install -r requirements.txt
```

#### Test Database Issues
```bash
# Clear test cache
rm -rf .pytest_cache
# Reset test database
rm test.db
```

#### Flaky Tests
```bash
# Run with retry
pytest --reruns 3 --reruns-delay 1
```

#### Slow Tests
```bash
# Skip slow tests
pytest -m "not slow"
```

## 📝 Writing New Tests

### Test Template
```python
import pytest
from app import create_app

class TestNewFeature:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()

    def test_feature_success(self):
        """Test successful case"""
        response = self.client.post('/api/endpoint',
            json={'key': 'value'})
        assert response.status_code == 200

    def test_feature_error(self):
        """Test error case"""
        response = self.client.post('/api/endpoint',
            json={'invalid': 'data'})
        assert response.status_code == 400
```

### Best Practices
1. **Descriptive names**: `test_what_when_expected`
2. **Single assertion focus**: One logical assertion per test
3. **Arrange-Act-Assert**: Clear test structure
4. **Use fixtures**: Avoid duplicate setup code
5. **Mock external services**: Keep tests isolated
6. **Test edge cases**: Null, empty, boundary values
7. **Document why**: Explain non-obvious test cases

## 📊 Test Metrics

### Current Statistics
- **Test Files**: 13
- **Test Functions**: 267
- **Assertions**: 800+
- **Fixtures**: 25
- **Execution Time**: ~12 seconds (full suite)
- **Quick Tests**: ~3 seconds

### Performance Goals
- Full suite: < 30 seconds
- Quick tests: < 5 seconds
- Coverage: > 90%
- Flakiness: < 1%

## 🤝 Contributing Tests

1. **Write test first**: TDD approach
2. **Follow patterns**: Use existing tests as templates
3. **Maintain coverage**: Don't decrease coverage
4. **Document complex tests**: Add docstrings
5. **Run locally**: Verify before committing
6. **Update this README**: Document new test categories

## Quick Commands Reference

```bash
# All tests
make test

# Quick tests
make test-quick

# With coverage
make test-coverage

# Specific module
pytest tests/unit/test_auth_routes.py

# Watch mode
pytest-watch

# Parallel execution
pytest -n auto

# Generate report
pytest --html=report.html
```

---

For more information, see [API-DOCUMENTATION.md](../API-DOCUMENTATION.md)
