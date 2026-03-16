"""
Smoke test for Azure OpenAI client. Skipped when AZURE_OPENAI_API_KEY is not set (CI-safe).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

_has_azure_key = bool(os.environ.get("AZURE_OPENAI_API_KEY", "").strip())


@pytest.mark.skipif(not _has_azure_key, reason="AZURE_OPENAI_API_KEY not set; skip to avoid calling Azure in CI")
def test_azure_client_generate_smoke():
    """When API key is set, call generate() with a tiny prompt. Do not assert response content."""
    from app.config import settings
    from rag.azure_client import AzureOpenAIClient

    client = AzureOpenAIClient(settings)
    result = client.generate("Say OK in one word.", max_tokens=10, temperature=0.0)
    assert isinstance(result, dict)
    assert "text" in result
    assert "raw_response" in result
