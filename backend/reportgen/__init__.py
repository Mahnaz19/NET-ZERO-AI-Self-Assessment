"""
Report generation: render recommendation report JSON to HTML and PDF.
No LLM calls — only deterministic rendering from stored report data.
"""

from .render import render_report_html, render_report_pdf_bytes

__all__ = ["render_report_html", "render_report_pdf_bytes"]
