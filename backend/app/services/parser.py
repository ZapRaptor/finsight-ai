"""
FinSight AI — PDF document parser.

Extracts and cleans text from SEC filings, annual reports, and other
financial PDFs.  Uses pdfplumber for table extraction and unstructured
for layout-aware paragraph parsing.

Produces chunked output suitable for embedding into Qdrant.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A single chunk of text extracted from a PDF."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        """Rough token count (~4 chars per token)."""
        return len(self.text) // 4


def _chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    metadata: Optional[dict[str, Any]] = None,
) -> list[TextChunk]:
    """Split text into overlapping chunks by token estimate.

    Parameters
    ----------
    chunk_size : int
        Target chunk size in approximate tokens.
    overlap : int
        Number of overlapping tokens between consecutive chunks.
    metadata : dict, optional
        Base metadata attached to every chunk.
    """
    base_meta = metadata or {}
    # Convert token targets to char counts (rough: 4 chars ≈ 1 token)
    char_chunk = chunk_size * 4
    char_overlap = overlap * 4

    chunks: list[TextChunk] = []
    start = 0

    while start < len(text):
        end = start + char_chunk
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    metadata={
                        **base_meta,
                        "chunk_index": len(chunks),
                        "char_start": start,
                        "char_end": min(end, len(text)),
                    },
                )
            )

        start += char_chunk - char_overlap

    return chunks


def parse_pdf_with_pdfplumber(file_path: str | Path) -> list[TextChunk]:
    """Extract text from a PDF using pdfplumber.

    Good for: tables, structured layouts, financial statements.
    """
    import pdfplumber

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    all_text_parts: list[str] = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Extract tables first
            tables = page.extract_tables()
            table_text = ""
            if tables:
                for table in tables:
                    rows = []
                    for row in table:
                        cleaned = [str(cell).strip() if cell else "" for cell in row]
                        rows.append(" | ".join(cleaned))
                    table_text += "\n".join(rows) + "\n\n"

            # Extract regular text
            page_text = page.extract_text() or ""

            combined = f"[Page {page_num}]\n"
            if page_text.strip():
                combined += page_text.strip() + "\n"
            if table_text.strip():
                combined += "\n[TABLE]\n" + table_text.strip() + "\n[/TABLE]\n"

            all_text_parts.append(combined)

    full_text = "\n\n".join(all_text_parts)
    logger.info(
        "pdfplumber extracted %d chars from %s (%d pages)",
        len(full_text),
        file_path.name,
        len(all_text_parts),
    )

    return _chunk_text(
        full_text,
        metadata={"source": file_path.name, "parser": "pdfplumber"},
    )


def parse_pdf_with_unstructured(file_path: str | Path) -> list[TextChunk]:
    """Extract text from a PDF using the `unstructured` library.

    Good for: complex multi-column layouts, narrative prose, SEC filings.
    """
    from unstructured.partition.pdf import partition_pdf

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    elements = partition_pdf(str(file_path))

    # Group elements into sections
    sections: list[str] = []
    current_section: list[str] = []

    for el in elements:
        el_type = type(el).__name__
        text = str(el).strip()

        if not text:
            continue

        if el_type in ("Title", "Header") and current_section:
            sections.append("\n".join(current_section))
            current_section = []

        current_section.append(text)

    if current_section:
        sections.append("\n".join(current_section))

    full_text = "\n\n".join(sections)
    logger.info(
        "unstructured extracted %d chars from %s (%d sections)",
        len(full_text),
        file_path.name,
        len(sections),
    )

    return _chunk_text(
        full_text,
        metadata={"source": file_path.name, "parser": "unstructured"},
    )


def parse_pdf(
    file_path: str | Path,
    strategy: str = "pdfplumber",
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[TextChunk]:
    """High-level PDF parsing entry point.

    Parameters
    ----------
    file_path : path
        Path to the PDF file.
    strategy : str
        'pdfplumber' (default) for tables/structured,
        'unstructured' for complex layouts,
        'both' to combine outputs.
    chunk_size : int
        Target tokens per chunk.
    overlap : int
        Overlap tokens between chunks.
    """
    file_path = Path(file_path)

    if strategy == "pdfplumber":
        return parse_pdf_with_pdfplumber(file_path)
    elif strategy == "unstructured":
        return parse_pdf_with_unstructured(file_path)
    elif strategy == "both":
        chunks_a = parse_pdf_with_pdfplumber(file_path)
        chunks_b = parse_pdf_with_unstructured(file_path)
        # Deduplicate by taking pdfplumber as primary, unstructured as supplement
        seen_texts = {c.text[:100] for c in chunks_a}
        for chunk in chunks_b:
            if chunk.text[:100] not in seen_texts:
                chunks_a.append(chunk)
        return chunks_a
    else:
        raise ValueError(f"Unknown parsing strategy: {strategy}")
