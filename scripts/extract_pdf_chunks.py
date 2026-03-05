from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

import pdfplumber


PII_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.MULTILINE)
PII_PHONE_RE = re.compile(r"\+?\d[\d\s\-]{7,}\d")
PII_COMPANY_RE = re.compile(r"\b(?:SC|NI|OC|LP|FC|SE)\d{5,}\b", re.IGNORECASE)

SECTION_HEADINGS = [
    "Management Summary",
    "Energy Saving Recommendations",
    "Energy Assessment Recommendations",
    "Current Annualised Energy Consumption on Site",
]


def _clean_text(text: str) -> str:
    text = PII_EMAIL_RE.sub("[redacted-email]", text)
    text = PII_PHONE_RE.sub("[redacted-phone]", text)
    text = PII_COMPANY_RE.sub("[redacted-company]", text)
    return text


def _split_into_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    lowered = text.lower()

    indices: List[Tuple[int, str]] = []
    for heading in SECTION_HEADINGS:
        idx = lowered.find(heading.lower())
        if idx != -1:
            indices.append((idx, heading))

    if not indices:
        return [("unknown", text)]

    indices.sort(key=lambda x: x[0])
    for i, (start_idx, heading) in enumerate(indices):
        end_idx = indices[i + 1][0] if i + 1 < len(indices) else len(text)
        section_text = text[start_idx:end_idx].strip()
        if section_text:
            sections.append((heading, section_text))

    return sections or [("unknown", text)]


def _chunk_text(section: str, text: str, max_chars: int = 3000) -> Iterable[dict]:
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            yield {
                "section": section,
                "text": chunk,
            }
        start = end


def run(pdf_dir: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records: List[dict] = []

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        full_text = "\n".join(pages_text)
        cleaned = _clean_text(full_text)
        sections = _split_into_sections(cleaned)

        for section_name, section_text in sections:
            for chunk in _chunk_text(section_name, section_text):
                chunk["source"] = pdf_path.name
                records.append(chunk)

    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text chunks from assessment PDFs.")
    parser.add_argument(
        "--pdf_dir",
        type=Path,
        required=True,
        help="Directory containing input PDF files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSONL path",
    )
    args = parser.parse_args()
    run(args.pdf_dir, args.out)


if __name__ == "__main__":
    main()

