"""LMArena leaderboard access through the Hugging Face datasets server."""

from __future__ import annotations

import re

import httpx

ARENA_DATASET = "lmarena-ai/leaderboard-dataset"
# The agent board reports a centered `score` instead of an Elo `rating`.
ARENA_BOARDS = ("text", "webdev", "agent")
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE = 100
# Rows arrive grouped by category, so paging stops once `overall` runs out. The cap
# bounds the damage if that grouping ever changes.
MAX_PAGES = 30
# Name fragments that mark how a model is served or licensed, not which model it is.
NOISE_TOKENS = frozenset({"contributor", "free", "preview"})

_PARENTHESES = re.compile(r"\([^)]*\)")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def _normalize_row(row: dict) -> dict:
    """Flatten one leaderboard row into the fields the report needs.

    Every field is optional on the wire: a row with a null `rating`, `vote_count` or
    `model_name` must not cost the whole board, so missing values stay `None` and
    `fetch_arena_board` drops the rows that cannot be used.
    """
    return {
        "model_name": row.get("model_name"),
        "organization": row.get("organization"),
        "license": row.get("license"),
        "value": row.get("rating") if row.get("rating") is not None else row.get("score"),
        "rank": int(row["rank"]) if row.get("rank") is not None else None,
        "publish_date": row.get("leaderboard_publish_date"),
    }


def fetch_arena_board(board: str) -> list[dict]:
    """Return the `overall` rows of one LMArena board, best value first."""
    entries: list[dict] = []
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        resp = httpx.get(
            ROWS_ENDPOINT,
            params={
                "dataset": ARENA_DATASET,
                "config": board,
                "split": "latest",
                "offset": offset,
                "length": PAGE_SIZE,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        rows = [item["row"] for item in payload.get("rows") or []]
        # Only the `overall` category is comparable across models.
        overall = [row for row in rows if row.get("category") == "overall"]
        # Stop on an empty page, or once `overall` runs out after we have seen some:
        # the rows are grouped by category but `overall` need not be the first block.
        if not rows or (entries and not overall):
            break
        for row in overall:
            entry = _normalize_row(row)
            if entry["model_name"] and entry["value"] is not None:
                entries.append(entry)
        if offset + PAGE_SIZE >= (payload.get("num_rows_total") or 0):
            break
    entries.sort(key=lambda entry: entry["value"], reverse=True)
    return entries


def normalize_arena_name(value: str) -> list[str]:
    """Split a model name into the tokens that identify the model itself.

    Parenthesised groups go first and whole: `(Max)`, `(High)` and `(0902)` mark a
    serving effort or a checkpoint inside one board row, so they split a model from
    itself rather than from another one. Digits stay separate tokens (`K3.1` becomes
    `k3`, `1`) because OpenCode IDs keep the same dots.
    """
    without_parentheses = _PARENTHESES.sub(" ", value.lower())
    tokens = _NON_ALPHANUMERIC.split(without_parentheses)
    return [token for token in tokens if token and token not in NOISE_TOKENS]


def _is_numeric_tail(tail: list[str]) -> bool:
    """Whether these trailing tokens can only be a checkpoint or version stamp.

    Only a date-like run of at least four digits (`0902`, `20261017`) is a stamp. A
    bare version number (`2`, `3`) is not: `GLM-5.2 (Max)` normalizes to
    `["glm", "5", "2"]`, and the shorter sibling `glm-5` must not read that `2` as
    its own checkpoint.
    """
    return bool(tail) and all(token.isdigit() and len(token) >= 4 for token in tail)


def match_arena_model(opencode_id: str, entries: list[dict]) -> dict | None:
    """Match an OpenCode model ID to the arena row that describes the same model.

    Two rules, in decreasing confidence, and the highest `value` wins among the
    candidates of the first rule that has any:

    1. Identical tokens, once effort markers and noise are dropped — the same model
       listed with a different effort level.
    2. The tokens of the model plus a checkpoint stamp — `DeepSeek-V4.1-Flash-20261017`
       is `deepseek-v4.1-flash` with a date appended. Only a four-digit-or-longer
       numeric token is a stamp, never a bare version number: `glm-5` ends on a
       version number itself, and reading the `.2` of `GLM-5.2 (Max)` as a stamp made
       it absorb that model's agent score. Catalog IDs do end on bare version numbers
       (`glm-5`, `gpt-5`), so the bound is what keeps this rule honest.

    Substring overlap is deliberately absent: `glm-5.3` is a substring of
    `GLM-5.3-Flash`, and a false positive here reports a plausible, wrong number.
    """
    target = normalize_arena_name(opencode_id)
    if not target:
        return None
    same_model: list[dict] = []
    dated_model: list[dict] = []
    for entry in entries:
        tokens = normalize_arena_name(entry["model_name"])
        if tokens == target:
            same_model.append(entry)
        elif tokens[: len(target)] == target and _is_numeric_tail(tokens[len(target) :]):
            dated_model.append(entry)
    candidates = same_model or dated_model
    return max(candidates, key=lambda entry: entry["value"]) if candidates else None
