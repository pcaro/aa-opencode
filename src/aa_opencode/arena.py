"""LMArena leaderboard access through the Hugging Face datasets server."""

from __future__ import annotations

import httpx

ARENA_DATASET = "lmarena-ai/leaderboard-dataset"
# The agent board reports a centered `score` instead of an Elo `rating`.
ARENA_BOARDS = ("text", "webdev", "agent")
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE = 100
# Rows arrive grouped by category, so paging stops once `overall` runs out. The cap
# bounds the damage if that grouping ever changes.
MAX_PAGES = 30


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
