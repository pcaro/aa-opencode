"""Render results as human-readable terminal output or JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

# Evaluation keys exposed by the free Artificial Analysis API.
INTELLIGENCE_KEY = "artificial_analysis_intelligence_index"
CODING_KEY = "artificial_analysis_coding_index"
MATH_KEY = "artificial_analysis_math_index"


def build_record(opencode_id: str, aa_model: dict | None) -> dict:
    """Flatten an AA model entry into a single record for one OpenCode model."""
    if aa_model is None:
        return {"opencode_id": opencode_id, "matched": False}

    evaluations = aa_model.get("evaluations") or {}
    pricing = aa_model.get("pricing") or {}
    creator = aa_model.get("model_creator") or {}
    return {
        "opencode_id": opencode_id,
        "matched": True,
        "name": aa_model.get("name"),
        "slug": aa_model.get("slug"),
        "creator": creator.get("name"),
        "intelligence_index": evaluations.get(INTELLIGENCE_KEY),
        "coding_index": evaluations.get(CODING_KEY),
        "math_index": evaluations.get(MATH_KEY),
        "output_tokens_per_second": aa_model.get("median_output_tokens_per_second"),
        "time_to_first_token_seconds": aa_model.get("median_time_to_first_token_seconds"),
        "price_blended_1m": pricing.get("price_1m_blended_3_to_1"),
        "price_input_1m": pricing.get("price_1m_input_tokens"),
        "price_output_1m": pricing.get("price_1m_output_tokens"),
    }


def _fmt(value: float | None, prefix: str = "", digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{prefix}{value:.{digits}f}"


def render_human(records: list[dict], show_unmatched: bool) -> None:
    console = Console()
    matched = [r for r in records if r["matched"]]
    unmatched = [r for r in records if not r["matched"]]

    table = Table(title="OpenCode models vs Artificial Analysis benchmarks")
    table.add_column("Model", style="bold")
    table.add_column("Creator")
    table.add_column("Intelligence", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Math", justify="right")
    table.add_column("Speed (tok/s)", justify="right")
    table.add_column("TTFT (s)", justify="right")
    table.add_column("Price $/1M", justify="right")

    for r in matched:
        table.add_row(
            r["opencode_id"],
            r["creator"] or "—",
            _fmt(r["intelligence_index"]),
            _fmt(r["coding_index"]),
            _fmt(r["math_index"]),
            _fmt(r["output_tokens_per_second"]),
            _fmt(r["time_to_first_token_seconds"]),
            _fmt(r["price_blended_1m"], prefix="$"),
        )

    console.print(table)

    if unmatched:
        console.print(f"[dim]{len(unmatched)} modelo(s) sin datos en Artificial Analysis.[/dim]")
        if show_unmatched:
            for r in unmatched:
                console.print(f"  [dim]• {r['opencode_id']}[/dim]")

    console.print(
        "[dim]Datos: https://artificialanalysis.ai/ (atribución requerida). "
        "Precio = blended 3:1 por 1M tokens.[/dim]"
    )


def render_json(records: list[dict], opencode_url: str) -> str:
    payload = {
        "source": "https://artificialanalysis.ai/",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "opencode_url": opencode_url,
        "models": records,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
