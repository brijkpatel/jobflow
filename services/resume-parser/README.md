# ResumeParser

A robust, production-ready Python framework for extracting structured information from resumes using multiple AI/ML strategies with automatic fallback.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-380%20passing-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

- 🎯 **Multi-Strategy Extraction** — Each field uses multiple strategies with automatic fallback (Regex → NER → LLM)
- 📝 **Multiple Formats** — Supports PDF, DOCX, and DOC files
- 📋 **19 Extracted Fields** — Name, email, phone, location, URLs, summary, skills, work experience, education, certifications, projects, interests, languages, awards, volunteer experience, publications, and computed analytics
- ⚙️ **Config-Driven** — Customize extraction strategies per field via configuration
- 🛡️ **Graceful Degradation** — Continues extraction even when individual strategies fail
- 🧪 **Well-Tested** — 380 tests including unit, integration, and E2E tests

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/brijkpatel/ResumeParser.git
cd ResumeParser

# Install dependencies with uv
uv sync --all-groups

# Run example
uv run python examples.py
```

```python
from framework import ResumeParserFramework

# Parse a resume (uses default config)
framework = ResumeParserFramework()
resume_data = framework.parse_resume("path/to/resume.pdf")

print(f"Name: {resume_data.name}")
print(f"Email: {resume_data.email}")
print(f"Skills: {', '.join(resume_data.skills)}")
print(f"Total experience: {resume_data.experience_analytics.total_years_experience:.1f} years")
```

## 📋 Quick Commands

```bash
# Run tests (fast - skips E2E tests)
uv run pytest -m "not e2e"

# Run all tests including E2E
uv run pytest

# Run with coverage
uv run pytest -m "not e2e" --cov=src --cov-report=html

# Format code
uv run black src/

# Type checking
uv run mypy src/
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📦 Installation & Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) — fast Python package manager

### Step-by-Step Setup

#### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Clone the Repository

```bash
git clone https://github.com/brijkpatel/ResumeParser.git
cd ResumeParser
```

#### 3. Install Dependencies

```bash
# Install all dependencies (production + dev) and create .venv automatically
uv sync --all-groups
```

> **Note:** `uv sync` reads `pyproject.toml` and creates a `.venv` in the project root automatically. No manual `python -m venv` needed.

#### 4. Configure API Keys

**⚠️ Required for LLM strategy (Gemini)**

Create a `.env` file in the project root:

```bash
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

#### 5. Verify Installation

```bash
# Run tests to verify everything works
uv run pytest -m "not e2e"

# Should see: 380 passed in ~2 seconds
```

### First-Time Model Download

The first time you run extraction, NER models (~500MB) will be downloaded automatically:

```bash
uv run python examples.py
```

Models are cached locally, so subsequent runs are fast.

## 🎯 Usage Examples

### Basic Usage

```python
from dotenv import load_dotenv
from framework import ResumeParserFramework

load_dotenv()

framework = ResumeParserFramework()
resume_data = framework.parse_resume("resumes/john_doe.pdf")

# Core contact info
print(f"Name: {resume_data.name}")
print(f"Email: {resume_data.email}")
print(f"Phone: {resume_data.phone}")
print(f"Location: {resume_data.location}")

# Online presence
print(f"LinkedIn: {resume_data.linkedin_url}")
print(f"GitHub: {resume_data.github_url}")

# Experience
for job in resume_data.work_experience:
    print(f"{job.title} @ {job.company} ({job.start_date} – {job.end_date})")

# Computed analytics
analytics = resume_data.experience_analytics
print(f"Total experience: {analytics.total_years_experience:.1f} years")
print(f"Career level: {analytics.career_level}")
print(f"Primary domain: {analytics.primary_domain}")

# Convert to dict/JSON
data_dict = resume_data.to_dict()
json_str = resume_data.to_json()
```

### Custom Configuration

```python
from framework import ResumeParserFramework
from config import ExtractionConfig
from interfaces import FieldType, StrategyType

custom_config = ExtractionConfig(
    strategy_preferences={
        FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
        FieldType.EMAIL: [StrategyType.REGEX],
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

load_dotenv()
framework = ResumeParserFramework()

results = []
for resume_file in Path("resumes/").glob("*.pdf"):
    try:
        data = framework.parse_resume(str(resume_file))
        results.append({
            "file": resume_file.name,
            "name": data.name,
            "email": data.email,
            "skills_count": len(data.skills) if data.skills else 0,
            "years_experience": data.experience_analytics.total_years_experience if data.experience_analytics else 0,
        })
    except Exception as e:
        print(f"Failed to parse {resume_file.name}: {e}")
```

### Error Handling

```python
from framework import ResumeParserFramework
from exceptions import UnsupportedFileFormatError, FileParsingError, FieldExtractionError

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
┌────────────────────────────────────────────────┐
│   ResumeParserFramework (Facade)               │  ← Entry point
├────────────────────────────────────────────────┤
│   File Parsers (PDF, DOCX)                     │  ← Parse documents to text
├────────────────────────────────────────────────┤
│   ResumeExtractor (Coordinator)                │  ← Orchestrates extraction
├────────────────────────────────────────────────┤
│   Field Extractors (19 fields)                 │  ← Extract specific fields
├────────────────────────────────────────────────┤
│   Strategies (Regex, NER, LLM)                 │  ← Extraction algorithms
└────────────────────────────────────────────────┘
```

**Design Patterns Used:**
- **Facade**: Simple interface (`ResumeParserFramework`) for complex subsystem
- **Coordinator**: Orchestrates multiple field extractors (`ResumeExtractor`)
- **Factory**: Creates extractor+strategy combinations (`create_extractor()`)
- **Strategy**: Interchangeable extraction algorithms (Regex, NER, LLM)
- **Chain of Responsibility**: Tries strategies in order until one succeeds

## 🔧 Configuration

### Default Strategy Order

| Field            | Strategy Order  | Notes |
|------------------|----------------|-------|
| Name             | NER → LLM      | NER is fast and accurate for names |
| Email            | REGEX → NER → LLM | Regex is sufficient for most emails |
| Phone            | REGEX → LLM    | Pattern matching works well |
| Skills           | LLM → NER      | LLM better at identifying technical skills |
| Work Experience  | LLM            | Structured extraction |
| Education        | LLM            | Structured extraction |
| Certifications   | LLM            | Structured extraction |
| Projects         | LLM            | Structured extraction |
| Analytics        | Computed       | Derived from work experience |

### Supported Strategies

- **REGEX**: Fast pattern matching (email, phone)
- **NER**: Named Entity Recognition using transformers (~500MB models)
- **LLM**: Large Language Model via Google Gemini (requires API key)

### File Formats

- ✅ `.pdf` — PDF documents (using pdfminer.six)
- ✅ `.docx` — Word documents (using python-docx)
- ✅ `.doc` — Legacy Word documents (using python-docx)

## 🧪 Testing

```bash
# Fast tests (recommended for development)
uv run pytest -m "not e2e"

# All tests including E2E (uses real NER models)
uv run pytest

# With coverage report
uv run pytest -m "not e2e" --cov=src --cov-report=html

# Run specific test file
uv run pytest src/extractors/tests/test_work_experience_extractor.py

# Run specific test class
uv run pytest src/framework/tests/test_resume_parser_framework.py::TestResumeParserFrameworkEndToEnd
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📁 Project Structure

```
ResumeParser/
├── src/
│   ├── config/              # Configuration management
│   ├── coordinators/        # ResumeExtractor (orchestration)
│   ├── exceptions/          # Custom exception classes
│   ├── extractors/          # Field extractors (19 fields)
│   │   └── strategies/      # Extraction strategies (Regex, NER, LLM)
│   ├── framework/           # ResumeParserFramework (facade)
│   ├── interfaces/          # Abstract base classes and protocols
│   ├── models/              # Data models (ResumeData + 9 sub-models)
│   ├── parsers/             # File parsers (PDF, Word)
│   └── utils/               # Logging and utilities
├── sample_resumes/          # Sample resume files for testing
├── examples.py              # Usage examples
├── pyproject.toml           # Project metadata and dependencies (uv)
├── uv.lock                  # Locked dependency versions
├── TESTING.md               # Testing documentation
└── README.md                # This file
```

## 🔍 Extracted Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full name |
| `email` | `str` | Email address |
| `phone` | `str` | Phone number |
| `location` | `str` | City, state, country |
| `linkedin_url` | `str` | LinkedIn profile URL |
| `github_url` | `str` | GitHub profile URL |
| `portfolio_url` | `str` | Personal website URL |
| `other_urls` | `List[str]` | Other URLs (Twitter, Behance, etc.) |
| `summary` | `str` | Professional summary / objective |
| `skills` | `List[str]` | Technical and professional skills |
| `work_experience` | `List[WorkExperienceEntry]` | Chronological work history |
| `education` | `List[EducationEntry]` | Degrees and academic history |
| `certifications` | `List[CertificationEntry]` | Professional certifications |
| `projects` | `List[ProjectEntry]` | Personal/professional projects |
| `interests` | `List[str]` | Hobbies and interests |
| `languages` | `List[str]` | Spoken/written languages |
| `awards` | `List[str]` | Awards and recognitions |
| `volunteer_experience` | `List[VolunteerEntry]` | Volunteer work |
| `publications` | `List[PublicationEntry]` | Published works |
| `experience_analytics` | `ExperienceAnalytics` | Computed analytics (years, level, etc.) |

## 🐛 Troubleshooting

### Issue: `GEMINI_API_KEY` not found

```bash
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_actual_api_key_here
```

### Issue: Module not found errors

```bash
# Ensure dependencies are installed
uv sync --all-groups

# Or activate the venv manually
source .venv/bin/activate
```

### Issue: Tests failing

```bash
# Clear pytest cache
uv run pytest --cache-clear

# Run with verbose output
uv run pytest -vv
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run tests: `uv run pytest -m "not e2e"`
5. Format code: `uv run black src/`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📝 Development Setup

```bash
# Install all dependencies (production + dev)
uv sync --all-groups

# Run linters
uv run black src/
uv run flake8 src/
uv run mypy src/

# Run tests
uv run pytest

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

## 📧 Contact

Brijesh Patel — [@brijkpatel](https://github.com/brijkpatel)

Project Link: [https://github.com/brijkpatel/ResumeParser](https://github.com/brijkpatel/ResumeParser)
