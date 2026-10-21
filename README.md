# aa-opencode

Compara los modelos que ofrece [OpenCode](https://opencode.ai) con los benchmarks de
[Artificial Analysis](https://artificialanalysis.ai): inteligencia, velocidad y precio, en
una sola tabla.

![Salida de aa-opencode con el catálogo Go](docs/aa-opencode.png)

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

# Ordenar por precio, velocidad o índice de código
aa-opencode --sort price
aa-opencode --sort speed
aa-opencode --sort coding

# Catálogo Zen en vez del Go (que es el de por defecto)
aa-opencode --catalog zen

# Salida JSON para programas externos
aa-opencode --format json

# Pasar la key explícitamente
aa-opencode --api-key "tu-key"
```

### Opciones

| Opción | Por defecto | Descripción |
| --- | --- | --- |
| `--api-key` | — | API key de Artificial Analysis. Tiene prioridad sobre las variables de entorno. |
| `--catalog {go,zen}` | `go` | Catálogo de modelos de OpenCode que se compara. También determina la fuente del precio y las etiquetas de la salida. |
| `--opencode-url` | — | Endpoint de modelos propio. Anula `--catalog`. |
| `--format {human,json}` | `human` | Formato de salida. |
| `--sort` | `intelligence` | Criterio de orden: `intelligence`, `coding`, `math`, `speed`, `ttft`, `price` o `name`. |
| `--top` | `3` | Modelos por categoría en el ranking calidad/precio. |
| `--show-unmatched` | — | Lista los modelos sin datos en Artificial Analysis (solo en la salida humana). |

## Salida

Las etiquetas de precio de las tres tablas llevan el nombre del catálogo elegido, así que
con `--catalog zen` verás `Zen $/1M` y `precio Zen` en lugar de las de Go.

### Tabla principal

Un modelo de OpenCode por fila, con los datos de Artificial Analysis y el precio que
cobra OpenCode. Ordenada por inteligencia por defecto.

```text
                         OpenCode models vs Artificial Analysis benchmarks
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Model                   ┃ Creator   ┃ Intelligence ┃ Coding ┃ Speed (tok/s) ┃ TTFT (s) ┃ Go $/1M ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ gemini-4-argon-contrib… │ Google    │         52.6 │      — │          81.4 │     24.1 │    $8.0 │
│ grok-4.7                │ SpaceXAI  │         46.4 │      — │          76.8 │     18.9 │    $3.0 │
│ mimo-v2.6-pro           │ Xiaomi    │         46.3 │      — │          41.8 │      2.6 │    $0.5 │
│ qwen3.8-max             │ Alibaba   │         45.4 │   76.2 │          38.9 │      1.9 │    $3.0 │
│ glm-5.3                 │ Z AI      │         44.8 │   74.8 │          68.0 │      3.0 │    $2.1 │
│ grok-4.6                │ SpaceXAI  │         44.3 │   76.8 │           0.0 │      0.0 │       — │
└─────────────────────────┴───────────┴──────────────┴────────┴───────────────┴──────────┴─────────┘
```

Un `—` significa que Artificial Analysis no publica ese dato para el modelo. Un `0.0` en
velocidad o TTFT suele ser un modelo que no han medido, no un modelo instantáneo.

### Ranking calidad/precio

Los tres modelos con mejor relación entre índice y precio de OpenCode, por categoría:
**Código** (índice de código), **Imágenes** (solo modelos multimodales) y **General**.

```text
                           Mejores calidad/precio (precio Go)
┏━━━━━━━━━━━┳━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Categoría ┃ # ┃ Modelo                     ┃ Índice ┃ Precio Go $/1M ┃ Calidad/Precio ┃
┡━━━━━━━━━━━╇━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Código    │ 1 │ muse-spark-1.2-contributor │   58.6 │           $0.1 │            469 │
│ Código    │ 2 │ muse-spark-1.3-contributor │   58.6 │           $0.1 │            469 │
│ Código    │ 3 │ mimo-v2.5                  │   60.2 │           $0.2 │            344 │
│ Imágenes  │ 1 │ muse-spark-1.2-contributor │   31.3 │           $0.1 │            250 │
│ Imágenes  │ 2 │ muse-spark-1.3-contributor │   31.3 │           $0.1 │            250 │
│ Imágenes  │ 3 │ claude-haiku-5-5           │   43.4 │           $0.2 │            217 │
│ General   │ 1 │ muse-spark-1.2-contributor │   31.3 │           $0.1 │            250 │
│ General   │ 2 │ muse-spark-1.3-contributor │   31.3 │           $0.1 │            250 │
│ General   │ 3 │ claude-haiku-5-5           │   43.4 │           $0.2 │            217 │
└───────────┴───┴────────────────────────────┴────────┴────────────────┴────────────────┘
```

`Calidad/Precio` es índice ÷ precio por millón de tokens. Cuanto más alto, mejor.

### Buenas ofertas

Modelos donde OpenCode los cobra más baratos que el precio público de referencia. El
ahorro se calcula como (precio AA − precio OpenCode) ÷ precio AA.

```text
                  Buenas ofertas Go (vs precio AA)
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Modelo              ┃ Precio AA $/1M ┃ Precio Go $/1M ┃ Ahorro % ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ mimo-v2.5           │           $0.5 │           $0.2 │      68% │
│ longcat-2.0         │           $1.3 │           $0.5 │      60% │
│ deepseek-v4.1-flash │           $0.5 │           $0.3 │      50% │
└─────────────────────┴────────────────┴────────────────┴──────────┘
```

### JSON

```json
{
  "source": "https://artificialanalysis.ai/",
  "generated_at": "2026-10-21T15:52:03.601197+00:00",
  "opencode_url": "https://opencode.ai/inference/go/v1/models",
  "models": [
    {
      "opencode_id": "mimo-v2.6-pro",
      "matched": true,
      "name": "MiMo-V2.6-Pro",
      "slug": "mimo-v2-6-pro",
      "creator": "Xiaomi",
      "intelligence_index": 46.3,
      "coding_index": null,
      "math_index": null,
      "output_tokens_per_second": 41.77,
      "time_to_first_token_seconds": 2.649,
      "price_blended_1m": 0.544,
      "price_input_1m": 0.435,
      "price_output_1m": 0.87,
      "multimodal": true,
      "go_price_blended_1m": 0.54375,
      "go_price_input_1m": 0.435,
      "go_price_output_1m": 0.87
    }
  ]
}
```

Los campos `price_*` son el precio público de Artificial Analysis y los `go_price_*` el que
cobra OpenCode. Los modelos sin datos en Artificial Analysis aparecen solo con
`opencode_id` y `matched: false`.

## Cómo funciona

1. Consulta el endpoint de modelos de OpenCode: `https://opencode.ai/inference/go/v1/models`
   para el catálogo Go (por defecto) o `https://opencode.ai/zen/v1/models` para Zen.
2. Consulta la API gratuita de Artificial Analysis (`/api/v2/data/llms/models`).
3. Empareja cada modelo de OpenCode con su entrada en Artificial Analysis: slug exacto,
   luego la subcadena más corta y por último el conjunto de tokens idéntico.
4. Añade el precio de OpenCode, leído de [models.dev](https://models.dev) y convertido a
   precio blended 3:1 por millón de tokens.
5. Muestra la tabla, el ranking calidad/precio y las mayores diferencias de precio.

## Limitaciones

- **El emparejamiento es heurístico**, no hay tabla de equivalencias escrita a mano. Un
  modelo mal emparejado da números creíbles y equivocados, así que conviene mirar la fila
  cuando aparece un modelo nuevo en el catálogo.
- **Los TTFT hay que leerlos con pinzas.** Algunos modelos salen con tiempos de primer
  token de cientos de segundos, que son artefactos del momento de la medición (colas, rate
  limits) y no latencia real.
- **No hay histórico.** Cada ejecución es una foto del momento.
- **No comprueba disponibilidad.** Si un modelo está de baja, no se entera.
- El precio por millón de tokens es una referencia de catálogo, no tu factura.

## Atribución

El uso de la API gratuita de Artificial Analysis requiere atribución a
https://artificialanalysis.ai/. Los precios de OpenCode provienen de https://models.dev/.
