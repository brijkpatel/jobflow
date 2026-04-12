# Test Data Directory

This directory contains **generated** test files for parser tests.

## Auto-Generation

All test files in this directory are **automatically generated** by pytest fixtures when you run tests. You don't need to commit these files to version control.

## Generated Files

### Valid Test Files
- `valid_resume.pdf` - Simple PDF resume for basic parsing tests
- `valid_resume.docx` - Simple DOCX resume for basic parsing tests
- `multipage.pdf` - Multi-page PDF for pagination testing
- `with_tables.pdf` - PDF containing table data
- `with_tables.docx` - DOCX containing table data
- `special_chars.pdf` - PDF with special characters (accents, symbols)
- `empty_content.docx` - DOCX with only whitespace paragraphs

### Invalid/Edge Case Files
- `empty.pdf` / `empty.docx` - Empty files
- `corrupted.pdf` / `corrupted.docx` - Corrupted/invalid file content
- `fake.pdf` / `fake.docx` - Text files with wrong extensions
- `sample.txt` - Plain text file (not PDF/DOCX)

## How It Works

When you run tests with pytest, the `setup_parser_test_data` fixture in `src/conftest.py` automatically:
1. Creates the data directory if it doesn't exist
2. Generates all necessary PDF files using `generate_test_pdfs.py`
3. Generates all necessary DOCX files using `generate_test_data.py`
4. Creates edge case files (empty, corrupted, fake, text files)

## Manual Regeneration

If you want to regenerate test files manually:

```bash
# Generate DOCX files
python src/parsers/tests/generate_test_data.py

# Generate PDF files
python src/parsers/tests/generate_test_pdfs.py
```

## Version Control

Add this directory to `.gitignore` since all files are generated:
```
src/parsers/tests/data/*.pdf
src/parsers/tests/data/*.docx
src/parsers/tests/data/*.txt
```

Keep only:
- `README.md` (this file)
- The generation scripts
