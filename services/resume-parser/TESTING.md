# Testing Guide

## Test Organization

The test suite is organized into:

- **Unit Tests**: Fast tests with mocked dependencies (~3 seconds)
- **E2E Tests**: End-to-end tests using real NER models (~144 seconds)

Total: 207 tests (202 unit/integration + 5 E2E)

## Quick Commands

### Run all tests (including E2E)
```bash
pytest
```
*Takes ~2.5 minutes due to E2E tests with real models*

### Run only fast tests (skip E2E)
```bash
pytest -m "not e2e"
```
*Recommended for development - takes ~3 seconds*

### Run only E2E tests
```bash
pytest -m e2e
```
*Use before commits to validate end-to-end behavior*

### Run tests by pattern
```bash
# Skip E2E by class name
pytest -k "not EndToEnd"

# Run only framework tests
pytest src/framework/tests/

# Run specific test file
pytest src/extractors/tests/test_email_extractor.py

# Run specific test
pytest src/framework/tests/test_resume_parser_framework.py::TestResumeParserFrameworkEndToEnd::test_end_to_end_with_default_config
```

### Run with coverage
```bash
# Fast (skip E2E)
pytest -m "not e2e" --cov=src --cov-report=html

# Full coverage (including E2E)
pytest --cov=src --cov-report=html
```

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests (uses real models)
- `@pytest.mark.slow` - Slow running tests

## CI/CD Recommendations

### Pull Request (Fast feedback)
```bash
pytest -m "not e2e"
```

### Nightly/Pre-merge (Complete validation)
```bash
pytest
```

## Test Structure

```
src/
├── coordinators/tests/          # 16 tests - ResumeExtractor
├── extractors/
│   ├── strategies/tests/        # 33 tests - Extraction strategies
│   └── tests/                   # 68 tests - Field extractors
├── framework/tests/             # 33 tests (28 unit + 5 E2E)
├── models/tests/                # 22 tests - Data models
└── parsers/tests/               # 35 tests (23 passed + 12 skipped)
```

## Notes

- **First E2E run**: Downloads ~500MB of NER models
- **Skipped tests**: 12 tests require special PDF/DOCX files not in repo
- **E2E tests**: Only mock file I/O, use real extractors and NER models
