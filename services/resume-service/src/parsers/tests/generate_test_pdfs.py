"""Script to generate test PDF files for parser tests."""

from pathlib import Path
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Create test data directory
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)


def create_simple_pdf():
    """Create a simple valid PDF file."""
    filename = data_dir / "valid_resume.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter)

    # Container for the 'Flowable' object
    elements: List[Any] = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    # Add content
    elements.append(Paragraph("Test Resume", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("John Doe", normal_style))
    elements.append(Paragraph("Email: john.doe@example.com", normal_style))
    elements.append(Paragraph("Phone: +1-234-567-8900", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Experience", heading_style))
    elements.append(Paragraph("Software Engineer at Tech Company", normal_style))
    elements.append(
        Paragraph(
            "Worked on various projects using Python, Java, and JavaScript.",
            normal_style,
        )
    )
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Skills", heading_style))
    elements.append(Paragraph("Python, Java, JavaScript, SQL, Git", normal_style))

    # Build PDF
    doc.build(elements)
    print(f"Created {filename.name}")


def create_pdf_with_tables():
    """Create a PDF with tables."""
    filename = data_dir / "with_tables.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter)

    elements: List[Any] = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Resume with Tables", styles["Heading1"]))
    elements.append(Spacer(1, 0.2 * inch))

    # Create a table
    data = [
        ["Name", "Jane Smith"],
        ["Email", "jane@example.com"],
        ["Phone", "+1-987-654-3210"],
    ]

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.beige),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Skills", styles["Heading2"]))
    elements.append(
        Paragraph("Python, Data Analysis, Machine Learning", styles["Normal"])
    )

    doc.build(elements)
    print(f"Created {filename.name}")


def create_multipage_pdf():
    """Create a multi-page PDF."""
    filename = data_dir / "multipage.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter)

    elements: List[Any] = []
    styles = getSampleStyleSheet()

    # Page 1
    elements.append(Paragraph("Multi-Page Resume", styles["Heading1"]))
    elements.append(Spacer(1, 0.2 * inch))

    for i in range(50):  # Add enough content for multiple pages
        elements.append(
            Paragraph(
                f"Line {i+1}: This is sample content to create a multi-page document.",
                styles["Normal"],
            )
        )
        if i % 10 == 9:
            elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    print(f"Created {filename.name}")


def create_pdf_with_special_chars():
    """Create a PDF with special characters."""
    filename = data_dir / "special_chars.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter)

    elements: List[Any] = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Resume with Special Characters", styles["Heading1"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Name: José García-Müller", styles["Normal"]))
    elements.append(Paragraph("Email: josé@example.com", styles["Normal"]))
    elements.append(Paragraph("Skills: C++, C#, Python", styles["Normal"]))
    elements.append(
        Paragraph("Description: Expert in AI/ML & data science", styles["Normal"])
    )

    doc.build(elements)
    print(f"Created {filename.name}")


if __name__ == "__main__":
    try:
        create_simple_pdf()
        create_pdf_with_tables()
        create_multipage_pdf()
        create_pdf_with_special_chars()
        print("\nAll test PDF files created successfully!")
    except Exception as e:
        print(f"Error creating test files: {e}")
        import traceback

        traceback.print_exc()
