"""Example usage of the Resume Parser Framework.

This module demonstrates how to use the config-driven Resume Parser Framework
with multiple fallback strategies for each field.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# This should be done once at the application entry point
load_dotenv()

# Add src directory to path to allow imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from framework import ResumeParserFramework


def example_with_default_config(filePath: str):
    """Example using the default configuration."""
    print("=" * 60)
    print("Example 1: Using Default Configuration")
    print("=" * 60)
    print(f"Processing: {filePath}")

    # Check if file exists
    if not Path(filePath).exists():
        print(f"❌ File not found: {filePath}")
        print("Skipping this example...\n")
        return

    # Create framework with default configuration
    # Default config tries multiple strategies in order:
    # - NAME: NER -> LLM
    # - EMAIL: REGEX -> NER -> LLM
    # - SKILLS: LLM -> NER
    framework = ResumeParserFramework()

    # Parse a PDF resume
    try:
        resume_data = framework.parse_resume(filePath)
        print("\n✅ Extracted Data:")
        print(resume_data.to_json())
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Resume Parser Framework - Usage Examples")
    print("=" * 60)
    print("\nNote: Place your resume files in 'sample_resumes/' directory")
    print("Supported formats: PDF, DOCX, DOC\n")

    # PDF resume file path
    example_with_default_config("sample_resumes/Brijesh_Patel_ATS.pdf")

    # Word resume file path
    example_with_default_config("sample_resumes/Brijesh_Patel_ATS.docx")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
