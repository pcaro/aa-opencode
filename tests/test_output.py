"""Tests for the record shape that joins Artificial Analysis with LMArena."""

from __future__ import annotations

from aa_opencode.output import arena_metadata, build_record


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
        "votes": 4403,
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
