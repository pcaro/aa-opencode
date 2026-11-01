"""Tests for the report shape: Arena record fields and the human tables."""

from __future__ import annotations

import pytest

from aa_opencode.output import _best_value, _render_arena_table, arena_metadata, build_record


def _record(model_id: str, **fields: object) -> dict:
    """One report record with the arena and price keys the tables read."""
    record: dict = {
        "opencode_id": model_id,
        "multimodal": False,
        "go_price_blended_1m": 1.0,
        "arena_text": None,
        "arena_webdev": None,
        "arena_agent": None,
        "arena_webdev_rank": None,
    }
    record.update(fields)
    return record


def _entry(
    model_name: str,
    value: float,
    rank: int | None = None,
    publish_date: str | None = "2026-10-28",
) -> dict:
    """One normalized arena row, as `fetch_arena_board` returns it."""
    return {
        "model_name": model_name,
        "organization": "Moonshot AI",
        "license": "Proprietary",
        "value": value,
        "rank": rank,
        "publish_date": publish_date,
    }


def test_build_record_keeps_arena_fields_when_the_model_is_missing_from_aa() -> None:
    """Arena and AA are independent sources, so the early return must carry them too."""
    boards = {"webdev": [_entry("Kimi K3.1 Pro (Max)", 1695.1, rank=9)]}

    record = build_record("kimi-k3.1-pro", None, boards)

    assert record["matched"] is False
    assert record["arena_webdev"] == 1695.1
    assert record["arena_webdev_name"] == "Kimi K3.1 Pro (Max)"
    assert record["arena_webdev_rank"] == 9
    assert record["arena_text"] is None


def test_build_record_fills_every_board_and_leaves_absences_empty() -> None:
    boards = {
        "text": [_entry("Kimi K3.1 Pro (Max)", 1464.5, rank=3)],
        "agent": [_entry("Kimi K3.1 Pro (Max)", 0.05, rank=4)],
    }
    aa_model = {
        "name": "Kimi K3.1 Pro",
        "evaluations": {"artificial_analysis_coding_index": 60.0},
    }

    record = build_record("kimi-k3.1-pro", aa_model, boards)

    assert record["matched"] is True
    assert record["coding_index"] == 60.0
    assert record["arena_text"] == 1464.5
    assert record["arena_agent"] == 0.05
    assert record["arena_webdev"] is None
    assert record["arena_webdev_name"] is None
    assert record["arena_webdev_rank"] is None


def test_build_record_accepts_an_empty_arena_payload() -> None:
    record = build_record("kimi-k3.1-pro", None, {})

    assert record["arena_text"] is None
    assert record["arena_agent_name"] is None


def test_arena_metadata_lists_the_boards_that_answered() -> None:
    boards = {"text": [_entry("Kimi K3.1 Pro (Max)", 1464.5)], "webdev": [], "agent": []}

    metadata = arena_metadata(boards)

    assert metadata == {
        "source": "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset",
        "license": "CC-BY-4.0",
        "boards": ["text", "webdev", "agent"],
        "published_at": "2026-10-28",
        "available": ["text"],
    }


def test_arena_metadata_without_data_has_no_publish_date() -> None:
    metadata = arena_metadata({"text": [], "webdev": [], "agent": []})

    assert metadata["published_at"] is None
    assert metadata["available"] == []


def test_best_value_puts_the_best_of_each_category_at_100() -> None:
    """An Elo (~1695) and an AA index (~60) only compare once each has its own base."""
    records = [
        _record("arena-best", arena_webdev=1695.0),
        _record("arena-half", arena_webdev=847.5),
        _record("aa-best", intelligence_index=60.0, go_price_blended_1m=2.0),
    ]

    webdev = _best_value(records, "arena_webdev", top_n=3, multimodal_only=False)
    general = _best_value(records, "intelligence_index", top_n=3, multimodal_only=False)

    assert [round(value, 1) for value, _ in webdev] == [100.0, 50.0]
    assert [round(value, 1) for value, _ in general] == [100.0]


def test_best_value_skips_models_without_quality_or_price() -> None:
    records = [
        _record("no-elo"),
        _record("no-price", arena_webdev=1600.0, go_price_blended_1m=None),
        _record("zero-price", arena_webdev=1600.0, go_price_blended_1m=0.0),
        _record("ranked", arena_webdev=1600.0),
    ]

    ranking = _best_value(records, "arena_webdev", top_n=5, multimodal_only=False)

    assert [record["opencode_id"] for _, record in ranking] == ["ranked"]


def test_arena_table_orders_by_webdev_when_sort_is_not_a_board(
    capsys: pytest.CaptureFixture[str],
) -> None:
    records = [
        _record("low-elo", arena_webdev=1500.0, arena_text=1400.0, arena_webdev_rank=9),
        _record("no-arena"),
        _record("high-elo", arena_webdev=1695.0, arena_text=1465.0, arena_webdev_rank=3),
    ]

    _render_arena_table(records, "coding")

    out = capsys.readouterr().out
    assert out.index("high-elo") < out.index("low-elo")
    assert "no-arena" not in out
    assert "1695" in out
    assert "1695.0" not in out


def test_arena_table_follows_an_arena_sort_key(capsys: pytest.CaptureFixture[str]) -> None:
    records = [
        _record("higher-text", arena_text=1490.0, arena_agent=-0.10),
        _record("higher-agent", arena_text=1450.0, arena_agent=0.20),
    ]

    _render_arena_table(records, "arena-text")
    by_text = capsys.readouterr().out
    _render_arena_table(records, "arena-agent")
    by_agent = capsys.readouterr().out

    assert by_text.index("higher-text") < by_text.index("higher-agent")
    assert by_agent.index("higher-agent") < by_agent.index("higher-text")


def test_arena_table_shows_agent_as_a_signed_score_not_a_percentage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    records = [
        _record("positive", arena_agent=0.20939685760341706),
        _record("negative", arena_agent=-0.10161684431257027),
        _record("rounded-zero", arena_agent=-0.0030051721572174742),
    ]

    _render_arena_table(records, "arena-agent")

    out = capsys.readouterr().out
    assert "+0.21" in out
    assert "-0.10" in out
    assert "-0.00" not in out
    assert "%" not in out


def test_arena_table_is_skipped_without_arena_data(capsys: pytest.CaptureFixture[str]) -> None:
    _render_arena_table([_record("bare")], "coding")

    assert capsys.readouterr().out == ""
