"""Render results as human-readable terminal output or JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from aa_opencode.arena import ARENA_BOARDS, match_arena_model
from aa_opencode.clients import blended_3_to_1

ARENA_SOURCE = "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset"
ARENA_LICENSE = "CC-BY-4.0"
ARENA_FIELDS = ("arena_text", "arena_webdev", "arena_agent")

# Sort names exposed by --sort, mapped to the record field they order by.
SORT_KEYS = {
    "intelligence": "intelligence_index",
    "coding": "coding_index",
    "speed": "output_tokens_per_second",
    "ttft": "time_to_first_token_seconds",
    "price": "price_blended_1m",
    "arena-text": "arena_text",
    "arena-webdev": "arena_webdev",
    "arena-agent": "arena_agent",
    "name": "opencode_id",
}

# Evaluation keys exposed by the free Artificial Analysis API.
INTELLIGENCE_KEY = "artificial_analysis_intelligence_index"
CODING_KEY = "artificial_analysis_coding_index"

# Best-value categories: (label, quality field, multimodal-only).
VALUE_CATEGORIES = [
    ("Código", "coding_index", False),
    ("WebDev", "arena_webdev", False),
    ("Imágenes", "intelligence_index", True),
    ("General", "intelligence_index", False),
]


def _arena_fields(opencode_id: str, arena_entries: dict[str, list[dict]]) -> dict:
    """Fill the Arena columns of one record, board by board."""
    matches = {
        board: match_arena_model(opencode_id, arena_entries.get(board, []))
        for board in ARENA_BOARDS
    }
    fields: dict = {}
    for board, match in matches.items():
        fields[f"arena_{board}"] = match["value"] if match is not None else None
        fields[f"arena_{board}_name"] = match["model_name"] if match is not None else None
    # WebDev is the board the report ranks models by, so it keeps its rank.
    webdev = matches["webdev"]
    fields["arena_webdev_rank"] = webdev["rank"] if webdev is not None else None
    return fields


def build_record(
    opencode_id: str, aa_model: dict | None, arena_entries: dict[str, list[dict]]
) -> dict:
    """Flatten one OpenCode model into a record: AA benchmarks plus Arena rows.

    Both sources are independent, and the Arena fields are added outside the AA
    branch: a model missing from Artificial Analysis can still hold an Elo.
    """
    if aa_model is None:
        record: dict = {"opencode_id": opencode_id, "matched": False}
    else:
        evaluations = aa_model.get("evaluations") or {}
        pricing = aa_model.get("pricing") or {}
        performance = aa_model.get("performance") or {}
        creator = aa_model.get("model_creator") or {}
        price_input = pricing.get("price_1m_input_tokens")
        price_output = pricing.get("price_1m_output_tokens")
        record = {
            "opencode_id": opencode_id,
            "matched": True,
            "name": aa_model.get("name"),
            "slug": aa_model.get("slug"),
            "creator": creator.get("name"),
            "intelligence_index": evaluations.get(INTELLIGENCE_KEY),
            "coding_index": evaluations.get(CODING_KEY),
            "output_tokens_per_second": performance.get("median_output_tokens_per_second"),
            "time_to_first_token_seconds": performance.get("median_time_to_first_token_seconds"),
            "price_blended_1m": blended_3_to_1(price_input, price_output),
            "price_input_1m": price_input,
            "price_output_1m": price_output,
        }
    record.update(_arena_fields(opencode_id, arena_entries))
    return record


def arena_metadata(arena_entries: dict[str, list[dict]]) -> dict:
    """Describe the Arena payload: attribution, boards that answered, publish date."""
    published_at = None
    for board in ARENA_BOARDS:
        rows = arena_entries.get(board) or []
        if rows:
            published_at = rows[0]["publish_date"]
            break
    return {
        "source": ARENA_SOURCE,
        "license": ARENA_LICENSE,
        "boards": list(ARENA_BOARDS),
        "published_at": published_at,
        "available": [board for board in ARENA_BOARDS if arena_entries.get(board)],
    }


def _fmt(value: float | None, prefix: str = "", suffix: str = "", digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{prefix}{value:.{digits}f}{suffix}"


def _best_value(
    records: list[dict], quality_key: str, top_n: int, multimodal_only: bool
) -> list[tuple[float, dict]]:
    """Rank models by quality/Go-price, the best of the category scoring 100.

    An Elo (~1695) and an AA index (~60) are not comparable numbers, so each
    category is normalized against its own best instead of sharing one raw ratio.
    """
    scored: list[tuple[float, dict]] = []
    for record in records:
        if multimodal_only and not record.get("multimodal"):
            continue
        quality = record.get(quality_key)
        price = record.get("go_price_blended_1m")
        if quality is None or price is None or price <= 0:
            continue
        scored.append((quality / price, record))
    if not scored:
        return []
    best = max(ratio for ratio, _ in scored)
    scored = [(ratio / best * 100, record) for ratio, record in scored]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top_n]


def _best_deals(records: list[dict], top_n: int) -> list[tuple[float, dict]]:
    """Rank models by how much cheaper Go is than the AA public price (percent)."""
    deals: list[tuple[float, dict]] = []
    for record in records:
        if not record["matched"]:
            continue
        aa_price = record.get("price_blended_1m")
        go_price = record.get("go_price_blended_1m")
        if aa_price is None or go_price is None or aa_price <= 0 or go_price <= 0:
            continue
        if go_price >= aa_price:
            continue
        discount = (aa_price - go_price) / aa_price * 100
        deals.append((discount, record))
    deals.sort(key=lambda item: item[0], reverse=True)
    return deals[:top_n]


def _render_value_table(records: list[dict], top_n: int, catalog: str) -> None:
    console = Console()
    table = Table(title=f"Mejores calidad/precio (precio {catalog.capitalize()})")
    table.add_column("Categoría", style="bold")
    table.add_column("#", justify="right")
    table.add_column("Modelo")
    table.add_column("Metric", justify="right")
    table.add_column(f"Precio {catalog.capitalize()} $/1M", justify="right")
    table.add_column("Value (max 100)", justify="right")

    for label, quality_key, multimodal_only in VALUE_CATEGORIES:
        for rank, (value, record) in enumerate(
            _best_value(records, quality_key, top_n, multimodal_only), start=1
        ):
            table.add_row(
                label,
                str(rank),
                record["opencode_id"],
                # An Elo is a four-digit number; an AA index reads with one decimal.
                _fmt(record[quality_key], digits=0 if quality_key.startswith("arena_") else 1),
                _fmt(record["go_price_blended_1m"], prefix="$"),
                _fmt(value),
            )

    console.print(table)


def _render_deals_table(records: list[dict], top_n: int, catalog: str) -> None:
    console = Console()
    table = Table(title=f"Buenas ofertas {catalog.capitalize()} (vs precio AA)")
    table.add_column("Modelo", style="bold")
    table.add_column("Precio AA $/1M", justify="right")
    table.add_column(f"Precio {catalog.capitalize()} $/1M", justify="right")
    table.add_column("Ahorro %", justify="right")

    for discount, record in _best_deals(records, top_n):
        table.add_row(
            record["opencode_id"],
            _fmt(record["price_blended_1m"], prefix="$"),
            _fmt(record["go_price_blended_1m"], prefix="$"),
            _fmt(discount, suffix="%", digits=0),
        )

    console.print(table)


def _fmt_score(value: float | None) -> str:
    """The agent board's centered score: signed, two decimals, never a percentage."""
    if value is None:
        return "—"
    rounded = round(value, 2)
    return f"{rounded:+.2f}" if rounded else "0.00"


def _render_arena_table(records: list[dict], sort_key: str) -> None:
    """Render LMArena human preference in its own table, one column per board."""
    arena_records = [
        record for record in records if any(record.get(field) is not None for field in ARENA_FIELDS)
    ]
    if not arena_records:
        return
    # Order by --sort when it names a board; WebDev is the board this report ranks by.
    field = SORT_KEYS[sort_key]
    if field not in ARENA_FIELDS:
        field = "arena_webdev"
    present = [record for record in arena_records if record.get(field) is not None]
    present.sort(key=lambda record: record[field], reverse=True)
    arena_records = present + [record for record in arena_records if record.get(field) is None]

    console = Console()
    table = Table(title="Arena (preferencia humana)")
    table.add_column("Model", style="bold")
    table.add_column("Text Elo", justify="right")
    table.add_column("WebDev Elo", justify="right")
    table.add_column("Agent score", justify="right")
    table.add_column("WebDev #", justify="right")

    for record in arena_records:
        rank = record.get("arena_webdev_rank")
        table.add_row(
            record["opencode_id"],
            _fmt(record.get("arena_text"), digits=0),
            _fmt(record.get("arena_webdev"), digits=0),
            _fmt_score(record.get("arena_agent")),
            str(rank) if rank is not None else "—",
        )

    console.print(table)


def render_human(
    records: list[dict],
    show_unmatched: bool,
    top_n: int,
    catalog: str,
    sort_key: str,
    index_version: float | None,
) -> None:
    console = Console()
    matched = [r for r in records if r["matched"]]
    unmatched = [r for r in records if not r["matched"]]
    price_label = catalog.capitalize()

    table = Table(title="OpenCode models vs Artificial Analysis benchmarks")
    table.add_column("Model", style="bold")
    table.add_column("Creator")
    table.add_column("Intelligence", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Speed (tok/s)", justify="right")
    table.add_column("TTFT (s)", justify="right")
    table.add_column(f"{price_label} $/1M", justify="right")

    for r in matched:
        table.add_row(
            r["opencode_id"],
            r["creator"] or "—",
            _fmt(r["intelligence_index"]),
            _fmt(r["coding_index"]),
            _fmt(r["output_tokens_per_second"]),
            _fmt(r["time_to_first_token_seconds"]),
            _fmt(r["go_price_blended_1m"], prefix="$"),
        )

    console.print(table)
    _render_arena_table(records, sort_key)
    _render_value_table(records, top_n, catalog)
    _render_deals_table(records, top_n, catalog)

    if unmatched:
        console.print(f"[dim]{len(unmatched)} modelo(s) sin datos en Artificial Analysis.[/dim]")
        if show_unmatched:
            for r in unmatched:
                console.print(f"  [dim]• {r['opencode_id']}[/dim]")

    console.print(
        "[dim]Datos: https://artificialanalysis.ai/ (atribución requerida). "
        f"Intelligence Index v{index_version:g}. "
        f"Precio {price_label} = blended 3:1 por 1M tokens. "
        f"Value: 100 = mejor de su categoría (métrica ÷ precio {price_label}). "
        f"Ahorro = (precio AA − precio {price_label}) ÷ precio AA.[/dim]"
    )
    console.print(
        "[dim]Arena: LMArena (lmarena-ai/leaderboard-dataset, CC-BY-4.0). "
        "Elo no comparable entre tableros. Agent = score centrado en 0, no un porcentaje.[/dim]"
    )


def render_json(
    records: list[dict],
    opencode_url: str,
    index_version: float | None,
    arena: dict,
) -> str:
    payload = {
        "source": "https://artificialanalysis.ai/",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "intelligence_index_version": index_version,
        "opencode_url": opencode_url,
        "arena": arena,
        "models": records,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
