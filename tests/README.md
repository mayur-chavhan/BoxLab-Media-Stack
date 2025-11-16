# arr Stack Manager Tests

This directory contains all test files for the arr Stack Manager project.

## 🧪 Test Structure

### Unit Tests

All test files follow the naming convention `test_*.py`:

#### Core Module Tests

- **test_config_store.py** - Configuration persistence and storage tests
- **test_validator.py** - Configuration validation tests
- **test_generator.py** - Docker Compose generation tests
- **test_docker_manager.py** - Docker operations tests
- **test_errors.py** - Error handling system tests

#### Model Tests

- **test_models.py** - Data model validation and behavior tests

#### Screen Tests

- **test_app.py** - Main application tests
- **test_dashboard.py** - Dashboard screen tests
- **test_service_selector.py** - Service selection screen tests
- **test_config_wizard.py** - Configuration wizard tests
- **test_stack_manager.py** - Stack management screen tests
- **test_deployment_monitor.py** - Deployment monitoring tests
- **test_log_viewer.py** - Log viewer tests
- **test_first_run.py** - First-run experience tests

#### Component Tests

- **test_components.py** - UI component tests

#### Integration Tests

- **test_controller.py** - Application controller integration tests
- **test_main.py** - Main entry point tests

## 🚀 Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_models.py
```

### Run with Coverage

```bash
pytest --cov=src/arr_stack_manager --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Tests Matching Pattern

```bash
pytest -k "test_configuration"
```

## 📊 Test Coverage

Current test coverage for core modules:

| Module               | Coverage | Status |
| -------------------- | -------- | ------ |
| models/\*            | 100%     | ✅     |
| core/generator.py    | 89%      | ✅     |
| core/validator.py    | 84%      | ✅     |
| core/config_store.py | 79%      | ✅     |
| utils/errors.py      | High     | ✅     |

**Overall Core Coverage: ~90%** (excluding docker_manager which requires Docker runtime)

## 🎯 Test Guidelines

### Writing New Tests

1. **Place test files in `tests/` directory**
2. **Name test files** with `test_` prefix (e.g., `test_feature.py`)
3. **Use descriptive test names** that explain what is being tested
4. **Follow the Arrange-Act-Assert pattern**
5. **Keep tests focused** - one concept per test
6. **Use fixtures** for common setup
7. **Mock external dependencies** (Docker, filesystem, etc.)

### Test Structure Example

```python
def test_feature_behavior():
    """Test that feature behaves correctly under normal conditions."""
    # Arrange
    config = Configuration(puid=1000, pgid=1000, ...)

    # Act
    result = config.get_selected_services()

    # Assert
    assert len(result) == 2
    assert "sonarr" in result
```

### Fixtures

Common fixtures are defined in `conftest.py` (if present) or within test files:

- `temp_config_dir` - Temporary configuration directory
- `sample_config` - Sample configuration object
- `sample_stack_config` - Sample stack configuration
- `mock_controller` - Mocked application controller

## 🔍 Test Categories

### Unit Tests

Focus on testing individual functions and classes in isolation.

### Integration Tests

Test how multiple components work together.

### UI Tests

Test Textual UI components and screens.

## 📁 Demo Scripts

The `demo-scripts/` directory contains standalone demo scripts for manual testing:

- Demo scripts for individual screens
- Interactive testing utilities
- Development helpers

## 🐛 Debugging Tests

### Run Tests with Debug Output

```bash
pytest -vv --tb=short
```

### Run Single Test with Full Traceback

```bash
pytest tests/test_models.py::TestConfiguration::test_add_service -vv
```

### Use pytest debugger

```bash
pytest --pdb
```

## 📝 Test Documentation

Each test file should include:

- Module docstring explaining what is being tested
- Test class docstrings for grouped tests
- Individual test docstrings explaining the test case

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Documentation Index](../docs/README.md) - All project documentation
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute (if exists)

## ✅ Test Checklist

Before committing:

- [ ] All tests pass
- [ ] New features have tests
- [ ] Test coverage is maintained or improved
- [ ] Tests are documented
- [ ] No skipped tests without good reason
