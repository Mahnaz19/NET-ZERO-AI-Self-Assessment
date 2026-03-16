"""
Azure OpenAI client: reads config from app settings (or os.environ if settings is None).
Returns model text and raw response. Raises RuntimeError if credentials are missing.
"""

from __future__ import annotations

import os
from typing import Any, Dict


def _get_config(settings: Any) -> tuple[str, str, str]:
    """Return (endpoint, api_key, deployment). Raises RuntimeError if any missing."""
    if settings is None:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
    else:
        endpoint = (getattr(settings, "AZURE_OPENAI_ENDPOINT", None) or "").strip()
        api_key = (getattr(settings, "AZURE_OPENAI_API_KEY", None) or "").strip()
        deployment = (getattr(settings, "AZURE_OPENAI_DEPLOYMENT", None) or "").strip()
    if not endpoint:
        raise RuntimeError(
            "Azure OpenAI is not configured: AZURE_OPENAI_ENDPOINT is missing. "
            "Set it in .env or environment to use the real LLM."
        )
    if not api_key:
        raise RuntimeError(
            "Azure OpenAI is not configured: AZURE_OPENAI_API_KEY is missing. "
            "Set it in .env or environment to use the real LLM."
        )
    if not deployment:
        raise RuntimeError(
            "Azure OpenAI is not configured: AZURE_OPENAI_DEPLOYMENT is missing. "
            "Set it in .env or environment to use the real LLM."
        )
    return endpoint, api_key, deployment


class AzureOpenAIClient:
    """
    Azure OpenAI chat client. Uses app config (backend/app/config.py settings).
    generate() returns dict with 'text' (model reply) and 'raw_response'.
    """

    def __init__(self, settings: Any):
        self._endpoint, self._api_key, self._deployment = _get_config(settings)
        self._endpoint = self._endpoint.rstrip("/")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Call Azure OpenAI chat completions. Returns dict with:
        - text: assistant message content (string)
        - raw_response: full response object from the API
        """
        try:
            from openai import AzureOpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai package is required for Azure OpenAI. Install with: pip install openai"
            ) from e

        client = AzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version="2024-02-15-preview",
        )
        response = client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": "You are an energy assessor assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = (response.choices[0].message.content or "").strip()
        return {"text": content, "raw_response": response}
