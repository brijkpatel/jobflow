# ResumeParser

A robust, production-ready Python framework for extracting structured information from resumes using multiple AI/ML strategies with automatic fallback.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-207%20passing-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

- 🎯 **Multi-Strategy Extraction** - Each field uses multiple strategies with automatic fallback (Regex → NER → LLM)
- 📝 **Multiple Formats** - Supports PDF, DOCX, and DOC files
- ⚙️ **Config-Driven** - Customize extraction strategies per field via configuration
- 🛡️ **Graceful Degradation** - Continues extraction even when individual strategies fail
- 🧪 **Well-Tested** - 207 tests including unit and E2E tests

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/brijkpatel/ResumeParser.git
cd ResumeParser

# Install dependencies
pip install -r requirements.txt

# Run example
python examples.py
```

```python
from framework import ResumeParserFramework

# Parse a resume (uses default config)
framework = ResumeParserFramework()
resume_data = framework.parse_resume("path/to/resume.pdf")

print(f"Name: {resume_data.name}")
print(f"Email: {resume_data.email}")
print(f"Skills: {', '.join(resume_data.skills)}")
```

## 📋 Quick Commands

```bash
# Run tests (fast - skips E2E tests)
pytest -m "not e2e"

# Run all tests including E2E
pytest

# Run with coverage
pytest -m "not e2e" --cov=src --cov-report=html

# Format code
black src/

# Type checking
mypy src/
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📦 Installation & Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/brijkpatel/ResumeParser.git
cd ResumeParser
```

#### 2. Create Virtual Environment

**Using venv (built-in):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Using pyenv (recommended):**
```bash
# Install Python 3.11 if not already installed
pyenv install 3.11.11

# Create virtual environment
pyenv virtualenv 3.11.11 resumeparser-env

# Activate
pyenv activate resumeparser-env

# Or set local Python version
pyenv local 3.11.11
```

#### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

#### 4. Configure API Keys

**⚠️ Required for LLM strategy (Gemini)**

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

**Getting your Gemini API key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in your `.env` file

**Note:** The `.env` file is already in `.gitignore` to prevent accidentally committing your API key.

#### 5. Verify Installation

```bash
# Run tests to verify everything works
pytest -m "not e2e"

# Should see: 202 passed in ~3 seconds
```

### First-Time Model Download

The first time you run extraction, NER models (~500MB) will be downloaded automatically:

```bash
# This will download models on first run
python examples.py
```

Models are cached locally, so subsequent runs are fast.

## 🎯 Usage Examples

### Basic Usage

```python
from dotenv import load_dotenv
from framework import ResumeParserFramework

# Load environment variables (do this once at app startup)
load_dotenv()

# Create framework with default config
framework = ResumeParserFramework()

# Parse a PDF resume
resume_data = framework.parse_resume("resumes/john_doe.pdf")

# Access extracted data
print(f"Name: {resume_data.name}")
print(f"Email: {resume_data.email}")
print(f"Skills: {resume_data.skills}")

# Convert to dict/JSON
data_dict = resume_data.to_dict()
json_str = resume_data.to_json()
```

**Note:** Always call `load_dotenv()` at the entry point of your application before using the framework. For tests, this is automatically handled in `conftest.py`.

### Custom Configuration

```python
from dotenv import load_dotenv
from framework import ResumeParserFramework
from config import ExtractionConfig
from interfaces import FieldType, StrategyType

# Load environment variables
load_dotenv()

# Define custom strategy order
custom_config = ExtractionConfig(
    strategy_preferences={
        FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
        FieldType.EMAIL: [StrategyType.REGEX],  # Email regex is very reliable
        FieldType.SKILLS: [StrategyType.LLM, StrategyType.NER],
    }
)

framework = ResumeParserFramework(config=custom_config)
resume_data = framework.parse_resume("resume.docx")
```

### Batch Processing

```python
from pathlib import Path
from dotenv import load_dotenv
from framework import ResumeParserFramework

# Load environment variables once
load_dotenv()

framework = ResumeParserFramework()
resume_dir = Path("resumes/")

results = []
for resume_file in resume_dir.glob("*.pdf"):
    try:
        data = framework.parse_resume(str(resume_file))
        results.append({
            "file": resume_file.name,
            "name": data.name,
            "email": data.email,
            "skills_count": len(data.skills) if data.skills else 0
        })
    except Exception as e:
        print(f"Failed to parse {resume_file.name}: {e}")

print(f"Successfully parsed {len(results)} resumes")
```

### Error Handling

```python
from framework import ResumeParserFramework
from exceptions import (
    UnsupportedFileFormatError,
    FileParsingError,
    FieldExtractionError
)

framework = ResumeParserFramework()

try:
    resume_data = framework.parse_resume("resume.pdf")
except FileNotFoundError:
    print("Resume file not found")
except UnsupportedFileFormatError as e:
    print(f"Unsupported file format: {e}")
except FileParsingError as e:
    print(f"Failed to parse file: {e}")
except FieldExtractionError as e:
    print(f"Failed to extract fields: {e}")
```

## 🏗️ Architecture

The framework uses a layered architecture with multiple design patterns:

```
┌─────────────────────────────────────────┐
│   ResumeParserFramework (Facade)        │  ← Entry point
├─────────────────────────────────────────┤
│   File Parsers (PDF, DOCX)              │  ← Parse documents to text
├─────────────────────────────────────────┤
│   ResumeExtractor (Coordinator)         │  ← Orchestrates extraction
├─────────────────────────────────────────┤
│   Field Extractors (Name, Email, Skills)│  ← Extract specific fields
├─────────────────────────────────────────┤
│   Strategies (Regex, NER, LLM)          │  ← Extraction algorithms
└─────────────────────────────────────────┘
```

**Design Patterns Used:**
- **Facade**: Simple interface (`ResumeParserFramework`) for complex subsystem
- **Coordinator**: Orchestrates multiple field extractors (`ResumeExtractor`)
- **Factory**: Creates extractor+strategy combinations (`create_extractor()`)
- **Strategy**: Interchangeable extraction algorithms (Regex, NER, LLM)
- **Chain of Responsibility**: Tries strategies in order until success

## 🔧 Configuration

### Default Strategy Order

| Field  | Strategy Order | Notes |
|--------|---------------|-------|
| Name   | NER → LLM | NER is fast and accurate for names |
| Email  | REGEX → NER → LLM | Regex is sufficient for most emails |
| Skills | LLM → NER | LLM better at identifying technical skills |

### Supported Strategies

- **REGEX**: Fast pattern matching (email extraction)
- **NER**: Named Entity Recognition using transformers (~500MB models)
- **LLM**: Large Language Model via Google Gemini (requires API key in `.env` file)

### File Formats

- ✅ `.pdf` - PDF documents (using PyMuPDF)
- ✅ `.docx` - Word documents (using python-docx)
- ✅ `.doc` - Legacy Word documents (using python-docx)

## 🧪 Testing

The project has comprehensive test coverage with 207 tests:

- **Unit Tests**: 202 tests (~3 seconds)
- **E2E Tests**: 5 tests (~2.5 minutes, uses real NER models)

**Environment Setup:** Tests automatically load `.env` via `conftest.py`, so API keys are available for all tests.

```bash
# Fast tests (recommended for development)
pytest -m "not e2e"

# All tests including E2E
pytest

# With coverage report
pytest -m "not e2e" --cov=src --cov-report=html
open htmlcov/index.html

# Run specific test file
pytest src/extractors/tests/test_email_extractor.py

# Run specific test
pytest src/framework/tests/test_resume_parser_framework.py::TestResumeParserFrameworkEndToEnd::test_end_to_end_with_default_config
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📁 Project Structure

```
ResumeParser/
├── src/
│   ├── config/              # Configuration management
│   ├── coordinators/        # ResumeExtractor (orchestration)
│   ├── exceptions/          # Custom exception classes
│   ├── extractors/          # Field extractors (Name, Email, Skills)
│   │   └── strategies/      # Extraction strategies (Regex, NER, LLM)
│   ├── framework/           # ResumeParserFramework (facade)
│   ├── interfaces/          # Abstract base classes and protocols
│   ├── models/              # Data models (ResumeData)
│   ├── parsers/             # File parsers (PDF, Word)
│   └── utils/               # Logging and utilities
├── examples.py              # Usage examples
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── pytest.ini              # Pytest configuration
├── TESTING.md              # Testing documentation
└── README.md               # This file
```

## 🔍 Extracted Fields

Currently supports extraction of:

- **Name**: Person's full name
- **Email**: Email address
- **Skills**: List of technical/professional skills

### Adding New Fields

To add a new field (e.g., phone number):

1. Add to `FieldType` enum in `interfaces/field_spec.py`
2. Create extractor in `extractors/` (e.g., `phone_extractor.py`)
3. Add strategy support in `extractors/factory.py`
4. Update configuration in `config/extraction_config.py`

## 🐛 Troubleshooting

### Issue: GEMINI_API_KEY not found error

```bash
# Ensure you have created a .env file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_actual_api_key_here

# Verify the file exists
cat .env
```

### Issue: Module not found errors

```bash
# Ensure you're in the project root and src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Or activate virtual environment
source venv/bin/activate
```

### Issue: Tests failing

```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Check Python version
python --version  # Should be 3.11+
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run tests: `pytest -m "not e2e"`
5. Format code: `black src/`
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (recommended)
pre-commit install

# Run linters
black src/
flake8 src/
mypy src/

# Run all tests
pytest

# Generate coverage report
pytest --cov=src --cov-report=html
```


## 📧 Contact

Brijesh Patel - [@brijkpatel](https://github.com/brijkpatel)

Project Link: [https://github.com/brijkpatel/ResumeParser](https://github.com/brijkpatel/ResumeParser)

---

**Note**: This is an educational/demonstration project. For production use, consider adding:
- API rate limiting for LLM strategies
- Caching layer for repeated extractions
- Database integration for storing results
- Web API/REST endpoints
- Docker containerization
- CI/CD pipeline