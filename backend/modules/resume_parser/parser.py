from __future__ import annotations

import io
import re
from typing import Optional


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract plain text from a PDF given its raw bytes.
    Uses pdfminer.six — pure-Python, no system deps.
    Falls back gracefully if the library is not installed.
    """
    try:
        from pdfminer.high_level import extract_text as _pdf_extract
        return _pdf_extract(io.BytesIO(file_bytes))
    except ImportError:
        # Fallback: very rough extraction by scanning for printable ASCII runs
        text = file_bytes.decode("latin-1", errors="ignore")
        printable = re.sub(r"[^\x20-\x7e\n]", " ", text)
        return printable


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract plain text from a DOCX given its raw bytes.
    Uses python-docx.
    """
    try:
        import docx  # python-docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs)
    except ImportError:
        # Fallback: strip XML from the docx zip
        import zipfile
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                with z.open("word/document.xml") as xml_file:
                    raw_xml = xml_file.read().decode("utf-8", errors="ignore")
            return re.sub(r"<[^>]+>", " ", raw_xml)
        except Exception:
            return ""


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Route to the correct extractor based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    if ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    # Plain text fallback
    return file_bytes.decode("utf-8", errors="ignore")
