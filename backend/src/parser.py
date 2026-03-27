from __future__ import annotations

import logging
import os
import re
import unicodedata
from typing import Any, Optional

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


def clean_text(text: str) -> str:
    """
    Normalize extracted text into a cleaner, more consistent representation.

    - Normalizes unicode (NFKC)
    - Removes excessive spaces/tabs
    - Collapses repeated newlines
    - Trims leading/trailing whitespace
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse spaces/tabs but preserve newlines.
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce runs of blank lines. Keep at most 2 consecutive newlines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_from_pdf(file: Any) -> str:
    """
    Extract full text from a PDF using pdfplumber.

    Loops through pages, extracts text, and returns a cleaned string.
    Returns "" on failure or when no extractable text is found.
    """
    stream = getattr(file, "file", file)  # FastAPI UploadFile exposes real stream at `.file`
    try:
        if hasattr(stream, "seek"):
            stream.seek(0)
    except Exception:
        # Best effort: if seek fails, pdfplumber may still read from current cursor.
        pass

    extracted_parts: list[str] = []
    try:
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                # Layout-aware extraction tends to preserve reading order better.
                page_text = ""
                for kwargs in (
                    {"layout": True, "use_text_flow": True, "x_tolerance": 2, "y_tolerance": 2},
                    {"layout": True, "use_text_flow": True, "x_tolerance": 3, "y_tolerance": 3},
                    {"layout": False, "use_text_flow": False, "x_tolerance": 3, "y_tolerance": 3},
                ):
                    try:
                        candidate = page.extract_text(**kwargs) or ""
                        if len(candidate) > len(page_text):
                            page_text = candidate
                    except Exception:
                        continue

                if page_text.strip():
                    extracted_parts.append(page_text)
    except Exception as exc:
        logger.exception("PDF parsing failed: %s", exc)
        return ""

    combined = clean_text("\n".join(extracted_parts))
    return combined


def extract_text_from_docx(file: Any) -> str:
    """
    Extract text from a DOCX using python-docx.
    Returns a cleaned string; returns "" on failure.
    """
    stream = getattr(file, "file", file)
    try:
        if hasattr(stream, "seek"):
            stream.seek(0)
    except Exception:
        pass

    try:
        doc = Document(stream)
        parts: list[str] = []
        for para in doc.paragraphs:
            if para.text and para.text.strip():
                parts.append(para.text)
        return clean_text("\n".join(parts))
    except Exception as exc:
        logger.exception("DOCX parsing failed: %s", exc)
        return ""


def load_input(file: Optional[Any], text: Optional[str]) -> str:
    """
    Load either a file (pdf/docx) or direct text input.
    Precedence: if `file` is provided and has a supported extension, use it.
    Otherwise, use `text`.
    """
    extracted = ""

    if file is not None:
        filename = getattr(file, "filename", None) or ""
        _, ext = os.path.splitext(filename.lower())

        if ext == ".pdf":
            extracted = extract_text_from_pdf(file)
        elif ext == ".docx":
            extracted = extract_text_from_docx(file)
        else:
            # Unsupported file type for the MVP.
            extracted = ""

    elif text is not None:
        extracted = text

    return clean_text(extracted or "")

