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

# Best-value categories: (label, quality field, multimodal-only).
VALUE_CATEGORIES = [
    ("Código", "coding_index", False),
    ("Imágenes", "intelligence_index", True),
    ("General", "intelligence_index", False),
]


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


def _best_value(
    records: list[dict], quality_key: str, top_n: int, multimodal_only: bool
) -> list[tuple[float, dict]]:
    """Rank matched models by quality/price ratio, returning (ratio, record) pairs."""
    scored: list[tuple[float, dict]] = []
    for record in records:
        if not record["matched"]:
            continue
        if multimodal_only and not record.get("multimodal"):
            continue
        quality = record.get(quality_key)
        price = record.get("price_blended_1m")
        if quality is None or price is None or price <= 0:
            continue
        scored.append((quality / price, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top_n]


def _render_value_table(records: list[dict], top_n: int) -> None:
    console = Console()
    table = Table(title="Mejores calidad/precio")
    table.add_column("Categoría", style="bold")
    table.add_column("#", justify="right")
    table.add_column("Modelo")
    table.add_column("Índice", justify="right")
    table.add_column("Precio $/1M", justify="right")
    table.add_column("Calidad/Precio", justify="right")

    for label, quality_key, multimodal_only in VALUE_CATEGORIES:
        for rank, (ratio, record) in enumerate(
            _best_value(records, quality_key, top_n, multimodal_only), start=1
        ):
            table.add_row(
                label,
                str(rank),
                record["opencode_id"],
                _fmt(record[quality_key]),
                _fmt(record["price_blended_1m"], prefix="$"),
                _fmt(ratio, digits=0),
            )

    console.print(table)


def render_human(records: list[dict], show_unmatched: bool, top_n: int) -> None:
    console = Console()
    matched = [r for r in records if r["matched"]]
    unmatched = [r for r in records if not r["matched"]]

    table = Table(title="OpenCode models vs Artificial Analysis benchmarks")
    table.add_column("Model", style="bold")
    table.add_column("Creator")
    table.add_column("Intelligence", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Speed (tok/s)", justify="right")
    table.add_column("TTFT (s)", justify="right")
    table.add_column("Price $/1M", justify="right")

    for r in matched:
        table.add_row(
            r["opencode_id"],
            r["creator"] or "—",
            _fmt(r["intelligence_index"]),
            _fmt(r["coding_index"]),
            _fmt(r["output_tokens_per_second"]),
            _fmt(r["time_to_first_token_seconds"]),
            _fmt(r["price_blended_1m"], prefix="$"),
        )

    console.print(table)
    _render_value_table(records, top_n)

    if unmatched:
        console.print(f"[dim]{len(unmatched)} modelo(s) sin datos en Artificial Analysis.[/dim]")
        if show_unmatched:
            for r in unmatched:
                console.print(f"  [dim]• {r['opencode_id']}[/dim]")

    console.print(
        "[dim]Datos: https://artificialanalysis.ai/ (atribución requerida). "
        "Precio = blended 3:1 por 1M tokens. Calidad/Precio = índice ÷ precio.[/dim]"
    )


def render_json(records: list[dict], opencode_url: str) -> str:
    payload = {
        "source": "https://artificialanalysis.ai/",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "opencode_url": opencode_url,
        "models": records,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
