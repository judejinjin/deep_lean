"""
PDF text extraction — tries PyMuPDF first, falls back to pdftotext.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from src.utils.logging import log


def _extract_pymupdf(path: str) -> str:
    """Extract text using PyMuPDF (fitz)."""
    import fitz  # PyMuPDF

    doc = fitz.open(path)
    pages: list[str] = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def _extract_pdftotext(path: str) -> str:
    """Extract text using pdftotext CLI (poppler-utils)."""
    import subprocess

    result = subprocess.run(
        ["pdftotext", "-layout", path, "-"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout


async def extract_text(path: str | Path) -> str:
    """Extract text from a PDF file.

    Tries PyMuPDF first, then pdftotext CLI if available.
    Returns empty string on failure.
    """
    path = str(Path(path).resolve())
    log.info("pdf_extract", path=path)

    # Try PyMuPDF first
    try:
        text = await asyncio.to_thread(_extract_pymupdf, path)
        if text.strip():
            log.info("pdf_extract_success", method="pymupdf", chars=len(text))
            return text
    except Exception as e:
        log.warning("pdf_pymupdf_failed", error=str(e))

    # Fall back to pdftotext if available
    if shutil.which("pdftotext"):
        try:
            text = await asyncio.to_thread(_extract_pdftotext, path)
            if text.strip():
                log.info("pdf_extract_success", method="pdftotext", chars=len(text))
                return text
        except Exception as e:
            log.warning("pdf_pdftotext_failed", error=str(e))

    log.warning("pdf_extract_empty", path=path)
    return ""
