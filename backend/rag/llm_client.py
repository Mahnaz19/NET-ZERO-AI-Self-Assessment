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
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Return a dict: either {executive_summary, recommendations} or {text, raw_response} for Azure."""
        ...


class MockLLM(BaseLLMClient):
    """
    Deterministic mock for dev and CI. Returns valid example JSON.
    Uses submission id from prompt to seed a stable message when present.
    """

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        # Try to extract submission id from prompt for deterministic seeding
        submission_id = 0
        match = re.search(r"submission[_\s]id[:\s]*(\d+)", prompt, re.I)
        if match:
            submission_id = int(match.group(1))

        # Read candidate lines from the prompt so mock output stays aligned
        # with deterministic candidates supplied by the pipeline and can return
        # a variable subset (like a real model would).
        candidate_rows: list[tuple[str, float]] = []
        for m in re.finditer(
            r"^- ([A-Z0-9_]+): .*?\| kwh_saved=([-+]?\d*\.?\d+) cost_saved=([-+]?\d*\.?\d+)",
            prompt,
            re.MULTILINE,
        ):
            code = m.group(1)
            kwh_saved = float(m.group(2))
            cost_saved = float(m.group(3))
            # Prioritize by monetary impact, with kWh as tie-breaker.
            score = (cost_saved * 1000.0) + kwh_saved
            candidate_rows.append((code, score))

        if not candidate_rows:
            candidate_rows = [
                ("LED_LIGHTING", 4.0),
                ("ENERGY_MANAGEMENT_BEHAVIOURAL", 3.0),
                ("SOLAR_PANELS", 2.0),
            ]

        # Highest impact first.
        candidate_rows.sort(key=lambda x: x[1], reverse=True)
        candidate_codes = [c for c, _ in candidate_rows]

        # Variable recommendation count (1..4, capped by available candidates).
        desired_n = (submission_id % 4) + 1
        n = min(max(1, desired_n), min(4, len(candidate_codes)))
        recommendations = []
        for i in range(n):
            measure_code = candidate_codes[i]
            priority = i + 1
            confidence = "high" if i == 0 else "medium"

            # Long-form deterministic text so the generated PDFs resemble the
            # structure/volume of the real (non-mock) recommendations.
            if measure_code in {"ENERGY_MANAGEMENT_BEHAVIOURAL", "HEATING_CONTROLS"}:
                recommendation_text = (
                    "The Carbon Trust estimate that companies can save up to 10% on energy costs "
                    "by no cost measures: good housekeeping measures which include:\n"
                    "1) Ensure all lights are switched off when not in use.\n"
                    "2) Ensure external doors are kept closed when not in use - this is to prevent "
                    "heat escaping through the open doors.\n"
                    "3) Move equipment away from radiators as equipment acts as a heat soak.\n"
                    "4) Monitor thermostatic radiator valve settings (TRVs) and reduce settings in "
                    "unoccupied spaces.\n"
                    "5) Ensure all PCs and monitors are switched off when not in use.\n"
                    "6) Switch off drinks fridges off fully at the plug when not required.\n"
                    "7) Electricity should be monitored with data from the electricity supplier; this data "
                    "can be analysed to confirm whether switch off procedures have been implemented effectively.\n\n"
                    f"Priority {priority}: Focus on controls and scheduling first to deliver rapid, low-risk "
                    "savings before considering higher-capex interventions."
                )
            elif measure_code in {"LED_LIGHTING", "LED_UPGRADE"}:
                recommendation_text = (
                    "Upgrade existing lighting to higher-efficiency LED fittings to reduce electricity usage "
                    "while maintaining required illuminance levels.\n\n"
                    "This recommendation supports:\n"
                    "- replacing outdated luminaires with LEDs that provide the same target lighting output,\n"
                    "- adding or optimising lighting controls (time schedules / occupancy sensing where applicable),\n"
                    "- ensuring any remaining lighting zones are correctly dimmed or switched off during low-occupancy periods.\n\n"
                    f"Priority {priority}: The measure is typically low disruption and can be phased to align "
                    "with maintenance schedules."
                )
            elif measure_code in {"SOLAR_PANELS", "SOLAR_PV"}:
                recommendation_text = (
                    "Installing a rooftop solar PV system would enable the site to generate a portion of its own "
                    "electricity, reducing reliance on the grid and lowering long-term operating costs.\n\n"
                    "Key considerations include:\n"
                    "- assessing roof suitability and shading conditions,\n"
                    "- confirming electrical capacity and integration with on-site demand,\n"
                    "- validating expected output using site-specific conditions.\n\n"
                    f"Priority {priority}: Prioritise PV where roof conditions and load profiles support high "
                    "self-consumption."
                )
            else:
                recommendation_text = (
                    f"Implement the {measure_code.replace('_', ' ').title()} measure as part of the "
                    "site's wider efficiency programme. Confirm scope with site-specific feasibility, "
                    "collect supplier quotes, and track post-implementation energy and carbon outcomes "
                    "against the current baseline."
                )

            recommendations.append(
                {
                    "measure_code": measure_code,
                    "score": 0.9 - i * 0.1,
                    "recommendation_text": recommendation_text,
                    "priority": priority,
                    "confidence": confidence,
                }
            )
        return {
            "executive_summary": f"Mock executive summary for submission {submission_id}. All numeric figures are from deterministic calculators; this text is for testing.",
            "recommendations": recommendations,
        }


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
    Factory: return Azure OpenAI client when AZURE_OPENAI_API_KEY is present, else MockLLM (for local/dev/CI).
    settings should be the app config (backend/app/config.py); env vars are used as fallback.
    """
    from .azure_client import AzureOpenAIClient

    endpoint = (getattr(settings, "AZURE_OPENAI_ENDPOINT", None) or os.environ.get("AZURE_OPENAI_ENDPOINT", "")).strip()
    api_key = (getattr(settings, "AZURE_OPENAI_API_KEY", None) or os.environ.get("AZURE_OPENAI_API_KEY", "")).strip()
    deployment = (
        (getattr(settings, "AZURE_OPENAI_DEPLOYMENT", None) or os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""))
    ).strip()
    if api_key and endpoint and deployment:
        return AzureOpenAIClient(settings)
    return MockLLM()
