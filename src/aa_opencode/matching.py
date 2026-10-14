"""Match OpenCode model IDs to Artificial Analysis model entries."""

from __future__ import annotations

import re


def normalize(value: str) -> str:
    """Lowercase, fold dots into dashes, and strip non-alphanumeric characters."""
    value = value.lower().replace(".", "-")
    return re.sub(r"[^a-z0-9-]", "", value)


def _tokens(value: str) -> frozenset[str]:
    return frozenset(normalize(value).split("-"))


def match_model(opencode_id: str, aa_models: list[dict]) -> dict | None:
    """Best-effort match of an OpenCode model ID to an AA model entry.

    Priority: exact slug, then shortest substring overlap, then identical token set.
    """
    target = normalize(opencode_id)

    # 1. Exact slug match.
    for model in aa_models:
        if normalize(model["slug"]) == target:
            return model

    # 2. Substring overlap, preferring the most specific (shortest) slug.
    candidates = [
        model
        for model in aa_models
        if target in normalize(model["slug"]) or normalize(model["slug"]) in target
    ]
    if candidates:
        return min(candidates, key=lambda m: len(normalize(m["slug"])))

    # 3. Identical token set (handles reordered names like "haiku-4-5" vs "4-5-haiku").
    target_tokens = _tokens(opencode_id)
    for model in aa_models:
        if _tokens(model["slug"]) == target_tokens:
            return model

    return None
