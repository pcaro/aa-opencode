"""Command-line interface for aa-opencode."""

from __future__ import annotations

import argparse
import os
import sys

from aa_opencode import __version__
from aa_opencode.clients import OPENCODE_MODELS_ENDPOINT, fetch_aa_models, fetch_opencode_models
from aa_opencode.matching import match_model
from aa_opencode.output import build_record, render_human, render_json

SORT_KEYS = {
    "intelligence": "intelligence_index",
    "coding": "coding_index",
    "math": "math_index",
    "speed": "output_tokens_per_second",
    "ttft": "time_to_first_token_seconds",
    "price": "price_blended_1m",
    "name": "opencode_id",
}


def resolve_api_key(cli_key: str | None) -> str:
    if cli_key:
        return cli_key
    for name in ("ARTIFICIAL_ANALYSIS_API_KEY", "AA_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise SystemExit(
        "Falta la API key de Artificial Analysis. Pásala con --api-key o define "
        "ARTIFICIAL_ANALYSIS_API_KEY (o AA_API_KEY)."
    )


def sort_records(records: list[dict], sort_key: str) -> list[dict]:
    field = SORT_KEYS[sort_key]
    reverse = sort_key != "name"
    matched = [r for r in records if r.get(field) is not None]
    unmatched = [r for r in records if r.get(field) is None]
    matched.sort(key=lambda r: r[field], reverse=reverse)
    return matched + unmatched


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa-opencode",
        description="Compara los modelos de OpenCode con los benchmarks de "
        "Artificial Analysis (inteligencia, velocidad y precio).",
    )
    parser.add_argument(
        "--api-key",
        help="API key de Artificial Analysis (por defecto lee ARTIFICIAL_ANALYSIS_API_KEY).",
    )
    parser.add_argument(
        "--opencode-url",
        default=OPENCODE_MODELS_ENDPOINT,
        help="Endpoint de modelos de OpenCode (por defecto %(default)s).",
    )
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="Formato de salida (por defecto human).",
    )
    parser.add_argument(
        "--sort",
        choices=tuple(SORT_KEYS),
        default="intelligence",
        help="Criterio de ordenación (por defecto intelligence).",
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help="Lista también los modelos sin datos en Artificial Analysis (solo human).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    api_key = resolve_api_key(args.api_key)

    aa_models = fetch_aa_models(api_key)
    opencode_ids = fetch_opencode_models(args.opencode_url)

    records = [
        build_record(model_id, match_model(model_id, aa_models)) for model_id in opencode_ids
    ]
    records = sort_records(records, args.sort)

    if args.format == "json":
        print(render_json(records, args.opencode_url))
    else:
        render_human(records, args.show_unmatched)

    return 0


if __name__ == "__main__":
    sys.exit(main())
