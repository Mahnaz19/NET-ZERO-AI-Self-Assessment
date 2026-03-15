"""
LLM client abstraction: MockLLM (dev/CI) and Azure OpenAI (real).
Uses env vars AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT for real client.
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Return a dict with at least executive_summary and recommendations (list)."""
        ...


class MockLLM(BaseLLMClient):
    """
    Deterministic mock for dev and CI. Returns valid example JSON.
    Uses submission id from prompt to seed a stable message when present.
    """

    def generate(self, prompt: str) -> Dict[str, Any]:
        # Try to extract submission id from prompt for deterministic seeding
        submission_id = 0
        match = re.search(r"submission[_\s]id[:\s]*(\d+)", prompt, re.I)
        if match:
            submission_id = int(match.group(1))
        # Deterministic recommendations based on seed
        n = max(2, (submission_id % 3) + 2)
        recommendations = []
        for i in range(n):
            recommendations.append({
                "measure_code": ["LED_UPGRADE", "HEATING_CONTROLS", "SOLAR_PV"][i % 3],
                "score": 0.9 - i * 0.1,
                "recommendation_text": f"Mock recommendation {i + 1} for submission {submission_id}. Prioritise this measure based on your site profile.",
                "priority": i + 1,
                "confidence": "high" if i == 0 else "medium",
            })
        return {
            "executive_summary": f"Mock executive summary for submission {submission_id}. All numeric figures are from deterministic calculators; this text is for testing.",
            "recommendations": recommendations,
        }


class AzureOpenAIClient(BaseLLMClient):
    """
    Azure OpenAI client. Calls chat completions and parses JSON from the reply.
    """

    def __init__(self, endpoint: str, api_key: str, deployment: str):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment

    def generate(self, prompt: str) -> Dict[str, Any]:
        try:
            from openai import AzureOpenAI
        except ImportError:
            logger.warning("openai package not installed; falling back to MockLLM behavior")
            return MockLLM().generate(prompt)

        client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2024-02-15-preview",
        )
        response = client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an energy assessor assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )
        content = (response.choices[0].message.content or "").strip()
        return _parse_llm_json(content)


def _parse_llm_json(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM reply; support raw JSON or markdown code block."""
    content = content.strip()
    # Try raw parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # Try to extract ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try first { ... } in content
    start = content.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[start : i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError("Could not parse valid JSON from LLM response")


def get_llm_client(settings: Any = None) -> BaseLLMClient:
    """
    Factory: return AzureOpenAIClient if AZURE_OPENAI_* env vars set, else MockLLM.
    settings can be the app config object; if None, uses os.environ.
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    deployment = (
        (getattr(settings, "AZURE_OPENAI_DEPLOYMENT", None) or os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""))
    ).strip()
    if settings and getattr(settings, "AZURE_OPENAI_ENDPOINT", None):
        endpoint = endpoint or getattr(settings, "AZURE_OPENAI_ENDPOINT", "")
    if settings and getattr(settings, "AZURE_OPENAI_API_KEY", None):
        api_key = api_key or getattr(settings, "AZURE_OPENAI_API_KEY", "")
    if endpoint and api_key and deployment:
        return AzureOpenAIClient(endpoint=endpoint, api_key=api_key, deployment=deployment)
    return MockLLM()
