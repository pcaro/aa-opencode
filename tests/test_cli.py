"""Tests for the CLI's tolerance to a failing LMArena board."""

from __future__ import annotations

import json

import httpx
import pytest

from aa_opencode import cli

AA_MODEL = {
    "name": "Kimi K3.1 Pro",
    "slug": "kimi-k3.1-pro",
    "evaluations": {"artificial_analysis_coding_index": 60.0},
    "pricing": {"price_1m_input_tokens": 1.0, "price_1m_output_tokens": 3.0},
    "performance": {
        "median_output_tokens_per_second": 100.0,
        "median_time_to_first_token_seconds": 0.5,
    },
    "model_creator": {"name": "Moonshot AI"},
}

TEXT_ROW = {
    "model_name": "Kimi K3.1 Pro (Max)",
    "organization": "Moonshot AI",
    "license": "Proprietary",
    "value": 1464.5,
    "rank": 3,
    "votes": 4403,
    "publish_date": "2026-10-28",
}


def _stub_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "fetch_aa_models", lambda api_key: ([AA_MODEL], 4.1))
    monkeypatch.setattr(cli, "fetch_opencode_models", lambda url: ["kimi-k3.1-pro"])
    monkeypatch.setattr(cli, "fetch_catalog_metadata", lambda catalog: {})


def _stub_arena(monkeypatch: pytest.MonkeyPatch, failing: set[str]) -> None:
    def fake_fetch(board: str) -> list[dict]:
        if board in failing:
            raise httpx.ConnectError("hf down")
        return [TEXT_ROW] if board == "text" else []

    monkeypatch.setattr(cli, "fetch_arena_board", fake_fetch)


def test_main_keeps_the_report_when_one_board_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_http(monkeypatch)
    _stub_arena(monkeypatch, failing={"webdev"})

    assert cli.main(["--api-key", "test", "--format", "json"]) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["arena"]["available"] == ["text"]
    assert payload["models"][0]["matched"] is True
    assert payload["models"][0]["arena_text"] == 1464.5
    assert payload["models"][0]["arena_webdev"] is None
    assert "«webdev»" in captured.err
    assert "hf down" in captured.err


@pytest.mark.parametrize(
    "error",
    [KeyError("model_name"), TypeError("'<' not supported"), ValueError("bad payload")],
)
def test_main_degrades_a_board_that_fails_to_normalize(
    error: Exception, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A malformed row costs one board, not the whole report."""
    _stub_http(monkeypatch)

    def fake_fetch(board: str) -> list[dict]:
        if board == "webdev":
            raise error
        return [TEXT_ROW] if board == "text" else []

    monkeypatch.setattr(cli, "fetch_arena_board", fake_fetch)

    assert cli.main(["--api-key", "test", "--format", "json"]) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["arena"]["available"] == ["text"]
    assert payload["models"][0]["arena_webdev"] is None
    assert "«webdev»" in captured.err


def test_main_warns_once_when_every_board_fails_to_normalize(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_http(monkeypatch)

    def fake_fetch(board: str) -> list[dict]:
        raise TypeError("'<' not supported between instances of 'NoneType' and 'float'")

    monkeypatch.setattr(cli, "fetch_arena_board", fake_fetch)

    assert cli.main(["--api-key", "test", "--format", "json"]) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["arena"]["available"] == []
    assert payload["models"][0]["matched"] is True
    assert captured.err.count("LMArena no responde") == 1


def test_main_warns_once_when_every_board_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_http(monkeypatch)
    _stub_arena(monkeypatch, failing={"text", "webdev", "agent"})

    assert cli.main(["--api-key", "test", "--format", "json"]) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["arena"]["available"] == []
    assert payload["arena"]["published_at"] is None
    assert payload["models"][0]["matched"] is True
    assert captured.err.count("LMArena no responde") == 1


def test_main_sorts_by_an_arena_board(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_http(monkeypatch)
    monkeypatch.setattr(
        cli, "fetch_opencode_models", lambda url: ["kimi-k3.1-pro", "hy4-preview", "beam-free"]
    )
    monkeypatch.setattr(cli, "fetch_aa_models", lambda api_key: ([], 4.1))
    board = [TEXT_ROW, {**TEXT_ROW, "model_name": "Hy4 preview", "value": 1490.0, "rank": 9}]
    monkeypatch.setattr(cli, "fetch_arena_board", lambda name: board if name == "text" else [])

    assert cli.main(["--api-key", "test", "--format", "json", "--sort", "arena-text"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert [model["opencode_id"] for model in payload["models"]] == [
        "hy4-preview",
        "kimi-k3.1-pro",
        "beam-free",
    ]
