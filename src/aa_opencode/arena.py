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
    """Flatten one leaderboard row into the fields the report needs."""
    return {
        "model_name": row["model_name"],
        "organization": row.get("organization"),
        "license": row.get("license"),
        "value": row["rating"] if "rating" in row else row.get("score"),
        "rank": int(row["rank"]) if row.get("rank") is not None else None,
        "votes": int(row["vote_count"] if "vote_count" in row else row["session_count"]),
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
        rows = [item["row"] for item in payload.get("rows", [])]
        # Only the `overall` category is comparable across models.
        overall = [row for row in rows if row.get("category") == "overall"]
        if page and not overall:
            break
        entries.extend(_normalize_row(row) for row in overall)
        if offset + PAGE_SIZE >= payload.get("num_rows_total", 0):
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
    """Whether these trailing tokens can only be a checkpoint or version stamp."""
    return bool(tail) and all(token.isdigit() for token in tail)


def match_arena_model(opencode_id: str, entries: list[dict]) -> dict | None:
    """Match an OpenCode model ID to the arena row that describes the same model.

    Two rules, in decreasing confidence, and the highest `value` wins among the
    candidates of the first rule that has any:

    1. Identical tokens, once effort markers and noise are dropped — the same model
       listed with a different effort level.
    2. The tokens of the model plus a numeric tail — `DeepSeek-V4.1-Flash-20261017`
       is `deepseek-v4.1-flash` with a date appended. A numeric tail is read as a
       checkpoint stamp, so an ID that ends on a bare version number would absorb the
       next one (`glm-5` onto `GLM-5.3`); no catalog ID does that today.

    Substring overlap is deliberately absent: `glm-5.3` is a substring of
    `GLM-5.3-Flash`, and a false positive here reports a plausible, wrong number.
    """
    target = normalize_arena_name(opencode_id)
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
