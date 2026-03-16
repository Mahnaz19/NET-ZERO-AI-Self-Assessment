"""
Render submission report JSON to HTML (Jinja2) and PDF (WeasyPrint with Playwright fallback).
No LLM calls — reads only deterministic report JSON.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_REPORT_TEMPLATE_NAME = "report.html"


def render_report_html(report_json: Dict[str, Any]) -> str:
    """
    Render a submission report JSON (from the recommendations pipeline) into HTML.
    Uses Jinja2 with a single report template. Does not perform any LLM or API calls.
    """
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(("html",)),
    )
    template = env.get_template(_REPORT_TEMPLATE_NAME)
    # Normalize so template always has .baseline and .recommendations
    report = dict(report_json)
    if "baseline" not in report or report["baseline"] is None:
        report["baseline"] = {}
    if "recommendations" not in report or report["recommendations"] is None:
        report["recommendations"] = []
    if "executive_summary" not in report:
        report["executive_summary"] = ""
    return template.render(report=report)


def render_report_pdf_bytes(report_json: Dict[str, Any]) -> bytes:
    """
    Convert report JSON to PDF bytes. Tries WeasyPrint first; falls back to Playwright if unavailable.
    No LLM calls — uses only the provided report JSON.
    """
    html = render_report_html(report_json)
    try:
        return _pdf_weasyprint(html)
    except Exception as e:
        logger.warning("WeasyPrint PDF conversion failed (%s), trying Playwright fallback", e)
    try:
        return _pdf_playwright(html)
    except Exception as e2:
        logger.exception("Playwright PDF fallback failed: %s", e2)
        raise RuntimeError(
            "PDF generation failed. Install WeasyPrint (e.g. pip install weasyprint) or Playwright (pip install playwright && playwright install chromium)."
        ) from e2


def _pdf_weasyprint(html: str) -> bytes:
    """Generate PDF using WeasyPrint. Raises if WeasyPrint not installed or fails."""
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()
    doc = HTML(string=html)
    return doc.write_pdf(font_config=font_config)


def _pdf_playwright(html: str) -> bytes:
    """Generate PDF using Playwright (Chromium). Use as fallback when WeasyPrint unavailable."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(format="A4", margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"})
            return pdf_bytes
        finally:
            browser.close()
