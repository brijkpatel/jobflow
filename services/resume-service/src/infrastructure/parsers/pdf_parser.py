from __future__ import annotations

from io import BytesIO

from pdfminer.high_level import extract_text

from domain.exceptions import FileParsingError


class PDFParser:
    def parse(self, file_bytes: bytes, filename: str) -> str:
        try:
            text = extract_text(BytesIO(file_bytes))
        except Exception as exc:  # pragma: no cover - pdfminer error surface
            raise FileParsingError(f"failed to parse {filename}") from exc
        cleaned = "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
        if not cleaned:
            raise FileParsingError(f"no text extracted from {filename}")
        return cleaned
