"""Extract clean text from resume PDFs."""
from __future__ import annotations
from typing import Union
import io
import pdfplumber


def extract_text(source: Union[bytes, str]) -> str:
    """source: raw PDF bytes or a file path."""
    if isinstance(source, (bytes, bytearray)):
        fh = io.BytesIO(source)
    else:
        fh = source
    parts = []
    with pdfplumber.open(fh) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
    text = "\n".join(parts)
    # normalise whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> list[str]:
    """Word-based chunking ~400 tokens per chunk with small overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        piece = " ".join(words[i:i + chunk_size])
        if piece.strip():
            chunks.append(piece)
        i += chunk_size - overlap
    return chunks
