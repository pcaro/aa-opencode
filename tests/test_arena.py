"""Tests for the LMArena matcher, row normalization and board pagination.

Fixtures mirror the rows served by the Hugging Face datasets API, raw keys
included, so the tests stay offline while still describing the real payloads.
"""

from __future__ import annotations

import pytest

from aa_opencode import arena


def _row(
    model_name: str,
    rating: float,
    votes: float,
    rank: int,
    category: str = "overall",
) -> dict:
    """One `webdev`/`text` row as the datasets API returns it."""
    return {
        "model_name": model_name,
        "organization": "Moonshot AI",
        "license": "Proprietary",
        "rating": rating,
        "rating_lower": rating - 4.0,
        "rating_upper": rating + 4.0,
        "variance": 4.2,
        "vote_count": votes,
        "rank": rank,
        "category": category,
        "leaderboard_publish_date": "2026-10-28",
    }


WEBDEV_ROWS = [
    _row("Kimi K3.1 Pro (Max)", 1695.1, 4403.0, 1),
    _row("Kimi K3.1 Pro (High)", 1680.0, 1200.0, 2),
    _row("Qwen3.8-Max (0902)", 1640.7, 3100.0, 3),
    _row("GLM-5.3 (Max)", 1610.5, 2700.0, 4),
    _row("DeepSeek-V4.1-Flash-20261017 (Max)", 1600.3, 2100.0, 5),
    _row("GLM-5.3-Flash", 1590.9, 1900.0, 6),
    _row("Muse Spark 1.2 (xHigh)", 1580.2, 1700.0, 7),
    _row("Claude Haiku 5.5 (High)", 1520.4, 1500.0, 8),
    _row("Hy4 preview", 1490.0, 900.0, 9),
]
# `match_arena_model` receives what `fetch_arena_board` produces, so matcher tests
# run on the normalized form of the same hand-written rows.
WEBDEV_ENTRIES = [arena._normalize_row(row) for row in WEBDEV_ROWS]

AGENT_ROW = {
    "model_name": "Claude Opus 5.5 (Max)",
    "organization": "Anthropic",
    "license": "Proprietary",
    "score": 0.20939685760341706,
    "score_ci_lower": 0.207,
    "score_ci_upper": 0.212,
    "observation_count": 41200,
    "session_count": 13584.0,
    "rank": 1,
    "category": "overall",
    "leaderboard_publish_date": "2026-10-28",
}


def test_normalize_arena_name_strips_parenthesized_effort_markers() -> None:
    tokens = arena.normalize_arena_name("Kimi K3.1 Pro (Max)")

    assert tokens == ["kimi", "k3", "1", "pro"]
    assert "max" not in tokens


def test_normalize_arena_name_drops_serving_noise_tokens() -> None:
    assert arena.normalize_arena_name("muse-spark-1.2-contributor") == ["muse", "spark", "1", "2"]
    assert arena.normalize_arena_name("Hy4 preview") == ["hy4"]


@pytest.mark.parametrize(
    ("opencode_id", "expected"),
    [
        ("kimi-k3.1-pro", "Kimi K3.1 Pro (Max)"),
        ("muse-spark-1.2-contributor", "Muse Spark 1.2 (xHigh)"),
        ("claude-haiku-5-5", "Claude Haiku 5.5 (High)"),
        ("hy4-preview", "Hy4 preview"),
        ("qwen3.8-max", "Qwen3.8-Max (0902)"),
        ("deepseek-v4.1-flash", "DeepSeek-V4.1-Flash-20261017 (Max)"),
        ("glm-5.3", "GLM-5.3 (Max)"),
    ],
)
def test_match_arena_model_returns_the_same_model(opencode_id: str, expected: str) -> None:
    match = arena.match_arena_model(opencode_id, WEBDEV_ENTRIES)

    assert match is not None
    assert match["model_name"] == expected


def test_match_arena_model_does_not_match_a_longer_model_name() -> None:
    """`glm-5.3` is a substring of `GLM-5.3-Flash`, but they are different models."""
    flash_only = [entry for entry in WEBDEV_ENTRIES if entry["model_name"] == "GLM-5.3-Flash"]

    assert arena.match_arena_model("glm-5.3", flash_only) is None


def test_match_arena_model_returns_none_for_an_absent_model() -> None:
    assert arena.match_arena_model("iceman-contributor-free", WEBDEV_ENTRIES) is None


def test_match_arena_model_returns_none_for_an_empty_board() -> None:
    assert arena.match_arena_model("kimi-k3.1-pro", []) is None


def test_match_arena_model_picks_the_highest_value_variant() -> None:
    entries = [
        arena._normalize_row(_row("Kimi K3.1 Pro (High)", 1680.0, 1200.0, 2)),
        arena._normalize_row(_row("Kimi K3.1 Pro (Max)", 1695.1, 4403.0, 1)),
    ]

    match = arena.match_arena_model("kimi-k3.1-pro", entries)

    assert match is not None
    assert match["model_name"] == "Kimi K3.1 Pro (Max)"


def test_normalize_row_flattens_a_rating_row() -> None:
    normalized = arena._normalize_row(WEBDEV_ROWS[0])

    assert normalized == {
        "model_name": "Kimi K3.1 Pro (Max)",
        "organization": "Moonshot AI",
        "license": "Proprietary",
        "value": 1695.1,
        "rank": 1,
        "votes": 4403,
        "publish_date": "2026-10-28",
    }
    assert isinstance(normalized["votes"], int)


def test_normalize_row_reads_score_and_sessions_from_the_agent_board() -> None:
    normalized = arena._normalize_row(AGENT_ROW)

    assert set(normalized) == set(arena._normalize_row(WEBDEV_ROWS[0]))
    assert normalized["value"] == pytest.approx(0.20939685760341706)
    assert normalized["votes"] == 13584
    assert isinstance(normalized["votes"], int)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def _payload(rows: list[dict], total: int) -> dict:
    return {
        "num_rows_total": total,
        "rows": [{"row_idx": index, "row": row} for index, row in enumerate(rows)],
    }


def _install_fake_get(monkeypatch: pytest.MonkeyPatch, pages: list[dict]) -> list[dict]:
    """Serve one payload per page offset and record every request."""
    calls: list[dict] = []

    def fake_get(url: str, params: dict, timeout: float) -> _FakeResponse:
        calls.append(params)
        return _FakeResponse(pages[params["offset"] // arena.PAGE_SIZE])

    monkeypatch.setattr(arena.httpx, "get", fake_get)
    return calls


def test_fetch_arena_board_keeps_only_overall_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        _row("Muse Spark 1.2 (xHigh)", 1580.2, 1700.0, 7),
        _row("Gemini 4 Carbon (High)", 1600.0, 900.0, 2, category="coding"),
        _row("Kimi K3.1 Pro (Max)", 1695.1, 4403.0, 1),
    ]
    calls = _install_fake_get(monkeypatch, [_payload(rows, total=3)])

    entries = arena.fetch_arena_board("webdev")

    assert [entry["model_name"] for entry in entries] == [
        "Kimi K3.1 Pro (Max)",
        "Muse Spark 1.2 (xHigh)",
    ]
    assert len(calls) == 1


def test_fetch_arena_board_stops_at_the_first_page_without_overall_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_page = [_row("Kimi K3.1 Pro (Max)", 1695.1, 4403.0, 1)]
    second_page = [_row("Gemini 4 Carbon (High)", 1600.0, 900.0, 2, category="coding")]
    calls = _install_fake_get(
        monkeypatch,
        [_payload(first_page, total=1000), _payload(second_page, total=1000)],
    )

    entries = arena.fetch_arena_board("webdev")

    assert [entry["model_name"] for entry in entries] == ["Kimi K3.1 Pro (Max)"]
    assert len(calls) == 2


def test_fetch_arena_board_respects_the_page_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    total = arena.MAX_PAGES * arena.PAGE_SIZE + 1
    pages = [
        _payload([_row(f"Model {index}", 1000.0 + index, 10.0, index)], total=total)
        for index in range(arena.MAX_PAGES + 5)
    ]
    calls = _install_fake_get(monkeypatch, pages)

    entries = arena.fetch_arena_board("text")

    assert len(calls) == arena.MAX_PAGES
    assert len(entries) == arena.MAX_PAGES
