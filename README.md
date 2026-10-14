# aa-opencode

Compara los modelos que ofrece [OpenCode](https://opencode.ai) con los benchmarks de
[Artificial Analysis](https://artificialanalysis.ai): índice de inteligencia, velocidad y
precio, en una sola tabla.

## Requisitos

- Python 3.10+
- Una API key gratuita de Artificial Analysis
  ([crear cuenta](https://artificialanalysis.ai/login) → generar API key)

## Instalación

```bash
uv tool install git+https://github.com/pcaro/aa-opencode
```

O, para desarrollo:

```bash
git clone https://github.com/pcaro/aa-opencode
cd aa-opencode
uv sync
```

## Uso

La API key se lee, por orden de prioridad, de:

1. El parámetro `--api-key`
2. La variable de entorno `ARTIFICIAL_ANALYSIS_API_KEY`
3. La variable de entorno `AA_API_KEY`

```bash
# Salida humana (por defecto), ordenada por inteligencia
aa-opencode

# Ordenar por precio o velocidad
aa-opencode --sort price
aa-opencode --sort speed

# Salida JSON para programas externos
aa-opencode --format json

# Pasar la key explícitamente
aa-opencode --api-key "tu-key"
```

### Salida humana

```
OpenCode models vs Artificial Analysis benchmarks
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Model            ┃ Creator   ┃ Intelligence ┃ Coding ┃ Math  ┃ Speed (tok/s) ┃ TTFT (s) ┃ Price $/1M ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ gpt-5.4          │ OpenAI    │ 57.6         │ 55.8   │ 87.2  │ 153.8         │ 14.9     │ $1.93      │
└──────────────────┴───────────┴──────────────┴────────┴───────┴───────────────┴──────────┴───────────┘
```

### Salida JSON

```json
{
  "source": "https://artificialanalysis.ai/",
  "generated_at": "2026-...",
  "opencode_url": "https://opencode.ai/zen/v1/models",
  "models": [
    {
      "opencode_id": "gpt-5.4",
      "matched": true,
      "name": "GPT-5.4",
      "creator": "OpenAI",
      "intelligence_index": 57.6,
      "coding_index": 55.8,
      "math_index": 87.2,
      "output_tokens_per_second": 153.8,
      "time_to_first_token_seconds": 14.9,
      "price_blended_1m": 1.93,
      "price_input_1m": 1.1,
      "price_output_1m": 4.4
    }
  ]
}
```

## Cómo funciona

1. Consulta `https://opencode.ai/zen/v1/models` para obtener la lista de modelos de OpenCode.
2. Consulta la API gratuita de Artificial Analysis (`/api/v2/data/llms/models`).
3. Empareja cada modelo de OpenCode con su entrada en Artificial Analysis (por slug, subcadena
   o conjunto de tokens).
4. Muestra inteligencia, velocidad y precio de cada modelo.

Los modelos de OpenCode sin datos en Artificial Analysis (modelos gratuitos, previews, etc.)
aparecen con `matched: false` en la salida JSON y se omiten de la tabla humana (usa
`--show-unmatched` para listarlos).

## Atribución

El uso de la API gratuita de Artificial Analysis requiere atribución a
https://artificialanalysis.ai/.
