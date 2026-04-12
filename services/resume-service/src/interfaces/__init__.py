"""Interfaces module for abstract base classes and protocols."""

from .file_parser import FileParser
from .field_extractor import FieldExtractor
from .extracting_strategy import StrategyType, FieldSpec, FieldType, ExtractionStrategy

__all__ = [
    "FileParser",
    "FieldExtractor",
    "StrategyType",
    "FieldSpec",
    "FieldType",
    "ExtractionStrategy",
]
