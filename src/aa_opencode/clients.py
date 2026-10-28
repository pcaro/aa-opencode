"""HTTP clients for Artificial Analysis and OpenCode."""

from __future__ import annotations

import httpx

AA_BASE = "https://artificialanalysis.ai"
AA_LLMS_ENDPOINT = f"{AA_BASE}/api/v2/language/models/free"
OPENCODE_MODELS_ENDPOINT = "https://opencode.ai/zen/v1/models"
GO_MODELS_ENDPOINT = "https://opencode.ai/inference/go/v1/models"
MODELS_DEV_ENDPOINT = "https://models.dev/api.json"

# OpenCode model catalogs and their models.dev metadata key.
CATALOGS = {
    "go": (GO_MODELS_ENDPOINT, "opencode-go"),
    "zen": (OPENCODE_MODELS_ENDPOINT, "opencode"),
}


def fetch_aa_models(api_key: str) -> tuple[list[dict], float | None]:
    """Return (models, intelligence index version) from the Artificial Analysis free API.

    The free endpoint is paginated, so every page is fetched and concatenated.
    """
    models: list[dict] = []
    version: float | None = None
    page = 1
    while True:
        resp = httpx.get(
            AA_LLMS_ENDPOINT,
            params={"page": page},
            headers={"x-api-key": api_key},
            timeout=30.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        version = payload.get("intelligence_index_version", version)
        models.extend(payload.get("data", []))
        if not (payload.get("pagination") or {}).get("has_more"):
            return models, version
        page += 1


def fetch_opencode_models(url: str) -> list[str]:
    """Return the list of model IDs offered by OpenCode."""
    resp = httpx.get(url, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()
    return [m["id"] for m in payload.get("data", [])]


def blended_3_to_1(input_price: float | None, output_price: float | None) -> float | None:
    """Compute the 3:1 blended price per 1M tokens from input/output prices."""
    if input_price is None or output_price is None:
        return None
    return (3 * input_price + output_price) / 4


def fetch_catalog_metadata(catalog: str) -> dict[str, dict]:
    """Return {model_id: {"modalities": set, "cost": dict}} from models.dev."""
    key = CATALOGS[catalog][1]
    resp = httpx.get(MODELS_DEV_ENDPOINT, timeout=30.0)
    resp.raise_for_status()
    models = resp.json().get(key, {}).get("models", {})
    return {
        model_id: {
            "modalities": set(model.get("modalities", {}).get("input", [])),
            "cost": model.get("cost") or {},
        }
        for model_id, model in models.items()
    }
