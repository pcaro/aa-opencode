"""HTTP clients for Artificial Analysis and OpenCode."""

from __future__ import annotations

import httpx

AA_BASE = "https://artificialanalysis.ai"
AA_LLMS_ENDPOINT = f"{AA_BASE}/api/v2/data/llms/models"
OPENCODE_MODELS_ENDPOINT = "https://opencode.ai/zen/v1/models"


def fetch_aa_models(api_key: str) -> list[dict]:
    """Return the list of LLM models from the Artificial Analysis free API."""
    resp = httpx.get(
        AA_LLMS_ENDPOINT,
        headers={"x-api-key": api_key},
        timeout=30.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != 200:
        raise RuntimeError(f"Artificial Analysis API error: {payload}")
    return payload.get("data", [])


def fetch_opencode_models(url: str) -> list[str]:
    """Return the list of model IDs offered by OpenCode."""
    resp = httpx.get(url, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()
    return [m["id"] for m in payload.get("data", [])]
