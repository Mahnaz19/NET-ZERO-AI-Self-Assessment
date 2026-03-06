from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Iterable, List, Tuple

import pdfplumber

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_DIR = REPO_ROOT / "data" / "raw" / "reports_sample"
DEFAULT_OUT = REPO_ROOT / "data" / "processed" / "reports_chunks.jsonl"


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


def _chunk_text(text: str, max_chars: int = 3000) -> Iterable[tuple[int, str]]:
    start = 0
    length = len(text)
    idx = 0
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            yield idx, chunk
            idx += 1
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

        chunk_index = 0
        for _section_name, section_text in sections:
            for _, chunk_text in _chunk_text(section_text):
                records.append({
                    "id": str(uuid.uuid4()),
                    "filename": pdf_path.name,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                })
                chunk_index += 1

    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text chunks from assessment PDFs.")
    parser.add_argument(
        "--pdf_dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help="Directory containing input PDF files (default: data/raw/reports_sample)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output JSONL path (default: data/processed/reports_chunks.jsonl)",
    )
    args = parser.parse_args()
    run(args.pdf_dir, args.out)


if __name__ == "__main__":
    main()

