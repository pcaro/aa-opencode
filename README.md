# aa-opencode

Compara los modelos que ofrece [OpenCode](https://opencode.ai) con los benchmarks de
[Artificial Analysis](https://artificialanalysis.ai): inteligencia, velocidad y precio, en
una sola tabla. Añade, aparte, la preferencia humana de [LMArena](https://lmarena.ai) en
tres tableros: texto, desarrollo web y agentes.

El demo es un cast de terminal versionado junto al código. Para verlo:

```bash
asciinema play docs/aa-opencode.cast
```

Y para regrabarlo tras un cambio de salida (`uvx asciinema` si no lo tienes
instalado):

```bash
asciinema rec docs/aa-opencode.cast --overwrite --headless \
  --window-size 120x58 --idle-time-limit 2 \
  -t "aa-opencode: catálogo Go frente a Artificial Analysis y LMArena" \
  -c "uv run aa-opencode --catalog go"
```

## Requisitos

- Python 3.10+
- Una API key gratuita de Artificial Analysis
  ([crear cuenta](https://artificialanalysis.ai/login) → generar API key)

El plan Free da 100 peticiones al día y cada ejecución gasta 4, así que salen unas 25
consultas diarias. Cuando se agotan, la herramienta no revienta: lo dice por stderr y te
indica cuánto falta para que se reponga la cuota.

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
# Salida humana (por defecto), ordenada por índice de código
aa-opencode

# Ordenar por precio, velocidad o índice de código
aa-opencode --sort price
aa-opencode --sort speed
aa-opencode --sort coding

# Ordenar por preferencia humana de LMArena (text, webdev o agent)
aa-opencode --sort arena-webdev

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
| `--sort` | `coding` | Criterio de orden: `coding`, `intelligence`, `speed`, `ttft`, `price`, `arena-text`, `arena-webdev`, `arena-agent` o `name`. |
| `--top` | `3` | Modelos por categoría en el ranking calidad/precio. |
| `--show-unmatched` | — | Lista los modelos sin datos en Artificial Analysis (solo en la salida humana). |

## Salida

Las etiquetas de precio de las cuatro tablas llevan el nombre del catálogo elegido, así que
con `--catalog zen` verás `Zen $/1M` y `precio Zen` en lugar de las de Go.

### Tabla principal

Un modelo de OpenCode por fila, con los datos de Artificial Analysis y el precio que
cobra OpenCode. Ordenada por índice de código por defecto, que es la métrica que más se
acerca a para qué se usa OpenCode.

```text
Aviso: ningún modelo tiene datos de «coding» ahora mismo, así que la tabla queda en el orden del catálogo. Prueba con otro --sort.
                           OpenCode models vs Artificial Analysis benchmarks
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Model                      ┃ Creator   ┃ Intelligence ┃ Coding ┃ Speed (tok/s) ┃ TTFT (s) ┃ Go $/1M ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ deepseek-v4.1-flash        │ DeepSeek  │            — │      — │         179.9 │      0.9 │    $0.3 │
│ deepseek-v4-pro            │ DeepSeek  │         23.1 │      — │          74.4 │      1.6 │    $1.0 │
│ glm-5.2                    │ Z AI      │            — │      — │          94.0 │      2.9 │    $2.1 │
│ glm-5.3                    │ Z AI      │         31.7 │      — │          71.8 │      2.1 │    $2.1 │
│ grok-4.7                   │ SpaceXAI  │         34.3 │      — │          94.2 │     30.6 │    $3.0 │
│ muse-spark-1.2-contributor │ Meta      │            — │      — │             — │        — │    $0.1 │
│ muse-spark-1.3-contributor │ Meta      │            — │      — │             — │        — │    $0.1 │
│ glm-5.3-flash              │ Z AI      │            — │      — │          72.8 │      1.7 │    $0.2 │
│ gpt-5.6-luna               │ OpenAI    │            — │      — │         126.5 │     94.7 │    $0.5 │
│ gpt-6-luna                 │ OpenAI    │         27.8 │      — │         121.6 │     76.6 │    $0.2 │
│ claude-haiku-5-5           │ Anthropic │         36.2 │      — │         240.0 │    341.1 │    $0.2 │
│ hy3                        │ Tencent   │            — │      — │          82.2 │      2.8 │    $0.2 │
│ …                          │ …         │            … │      … │             … │        … │       … │
└────────────────────────────┴───────────┴──────────────┴────────┴───────────────┴──────────┴─────────┘
```

Esta salida está capturada mientras Artificial Analysis recomputa el índice de código tras
el salto a v5, así que la columna Coding sale entera a `—` y la tabla queda en el orden del
catálogo. Cuando el índice vuelve, la tabla se ordena sola.


Un `—` significa que Artificial Analysis no publica ese dato para el modelo.

El Intelligence Index va por versiones mayores y **las puntuaciones no son comparables entre
versiones**: la versión vigente sale en el pie de la tabla (hoy `v5`). Además, Artificial
Analysis puntúa por tandas y recomputa índices enteros cuando cambia la metodología — el de
código, por ejemplo, se deriva de las evaluaciones del Intelligence Index y se queda vacío
mientras lo recalculan. Cuando el campo por el que ordenas no tiene ni un dato, la tool lo
avisa por stderr y deja la tabla en el orden del catálogo, en vez de fingir un orden.

### Tabla Arena

LMArena mide preferencia humana en comparaciones por pares. Es una señal distinta de la de
Artificial Analysis: aquí no hay respuesta correcta, hay votos. La tabla sale solo con los
modelos del catálogo que tienen fila en algún tablero.

```text
                          Arena (preferencia humana)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Model                      ┃ Text Elo ┃ WebDev Elo ┃ Agent score ┃ WebDev # ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ kimi-k3.1-pro              │        — │       1695 │       +0.06 │        9 │
│ gemini-4-argon             │     1529 │       1679 │       +0.11 │       11 │
│ qwen3.8-max                │     1483 │       1676 │        0.00 │       13 │
│ deepseek-v4.1-flash        │     1465 │       1665 │       +0.03 │       16 │
│ kimi-k3                    │     1476 │       1656 │       +0.01 │       18 │
│ muse-spark-1.3-contributor │     1491 │       1656 │       +0.03 │       19 │
│ grok-4.7                   │     1398 │       1637 │       +0.02 │       21 │
│ mimo-v2.6-flash            │     1451 │       1637 │       +0.01 │       22 │
│ hy4-preview                │        — │       1631 │       +0.01 │       23 │
│ mimo-v2.6-pro              │     1491 │       1625 │       +0.03 │       25 │
│ glm-5.3                    │     1474 │       1623 │       +0.01 │       27 │
│ glm-5.3-flash              │     1473 │       1607 │       -0.02 │       32 │
│ glm-5.2                    │     1470 │       1606 │       +0.01 │       33 │
│ claude-haiku-5-5           │     1401 │       1589 │       +0.01 │       36 │
│ minimax-m3.1-flash         │        — │       1582 │       -0.04 │       38 │
│ deepseek-v4-pro            │     1451 │       1582 │        0.00 │       39 │
│ gpt-6-luna                 │     1389 │       1579 │       +0.02 │       41 │
│ step-5-preview             │     1443 │       1571 │       -0.03 │       42 │
│ muse-spark-1.2-contributor │     1483 │       1534 │       -0.08 │       54 │
│ gpt-5.6-luna               │     1431 │       1519 │           — │       59 │
│ hy3                        │     1439 │       1505 │       -0.07 │       64 │
│ minimax-m3                 │     1431 │       1483 │       -0.10 │       69 │
│ kimi-k2.7-code             │        — │       1474 │           — │       73 │
│ qwen3.7-plus               │     1455 │          — │       -0.07 │        — │
└────────────────────────────┴──────────┴────────────┴─────────────┴──────────┘
```

- **Text Elo** y **WebDev Elo** son el rating Elo de los tableros `text` y `webdev`. Más
  alto es mejor.
- **Agent score** es el tablero `agent`, que no publica Elo sino un score centrado en 0
  (rango aproximado de −0,21 a +0,21). Sale con signo y dos decimales. **No es un
  porcentaje**: un `+0.10` no es un 10% de nada.
- **WebDev #** es el puesto del modelo en el tablero `webdev`, dentro de la categoría
  `overall`.

El Elo **no es comparable entre tableros**. Un 1695 en `webdev` y un 1465 en `text` no
significan que el modelo sea 230 puntos mejor en desarrollo web: cada tablero tiene su
propia escala. El `Agent score` tampoco se compara con un Elo.

La tabla se ordena por el tablero que pidas con `--sort`; si el criterio no es un tablero,
ordena por WebDev Elo. Un `—` significa que el modelo no tiene fila en ese tablero. Los
modelos sin datos en Artificial Analysis también aparecen aquí si LMArena los tiene: las
dos fuentes son independientes.

### Ranking calidad/precio

Los tres modelos con mejor relación entre calidad y precio de OpenCode, por categoría:
**Código** (índice de código), **WebDev** (Elo de LMArena), **Imágenes** (índice de
inteligencia, solo modelos multimodales) y **General** (índice de inteligencia).

```text
                            Mejores calidad/precio (precio Go)
┏━━━━━━━━━━━┳━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Categoría ┃ # ┃ Modelo                     ┃ Metric ┃ Precio Go $/1M ┃ Value (max 100) ┃
┡━━━━━━━━━━━╇━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ WebDev    │ 1 │ muse-spark-1.3-contributor │   1656 │           $0.1 │           100.0 │
│ WebDev    │ 2 │ muse-spark-1.2-contributor │   1534 │           $0.1 │            92.6 │
│ WebDev    │ 3 │ mimo-v2.6-flash            │   1637 │           $0.2 │            70.6 │
│ Imágenes  │ 1 │ claude-haiku-5-5           │   36.2 │           $0.2 │           100.0 │
│ Imágenes  │ 2 │ mimo-v2.6-flash            │   26.7 │           $0.2 │            84.3 │
│ Imágenes  │ 3 │ gpt-6-luna                 │   27.8 │           $0.2 │            76.8 │
│ General   │ 1 │ claude-haiku-5-5           │   36.2 │           $0.2 │           100.0 │
│ General   │ 2 │ mimo-v2.6-flash            │   26.7 │           $0.2 │            84.3 │
│ General   │ 3 │ gpt-6-luna                 │   27.8 │           $0.2 │            76.8 │
└───────────┴───┴────────────────────────────┴────────┴────────────────┴─────────────────┘
```

En esta captura no aparece la categoría Código porque el índice de código de Artificial
Analysis está vacío (ver la tabla principal); cuando vuelve, sale como las demás.

`Metric` es la calidad con la que se calcula la categoría: un índice de Artificial
Analysis o el Elo de LMArena. `Value` es esa métrica dividida por el precio y **relativa a
la mejor de su categoría**: el modelo con mejor relación de cada categoría saca 100 y el
resto se escala contra él. No es un porcentaje ni una nota absoluta sobre 100, es una
posición dentro de su categoría.

Antes esta columna era el ratio crudo. Con dos fuentes en la misma tabla eso deja de
funcionar: un Elo de WebDev ronda 1695 y un índice de Artificial Analysis ronda 60, así
que el ratio crudo ponía dos escalas incomparables en la misma columna y el Elo siempre
ganaba. Normalizar cada categoría contra su propio mejor deja las filas comparables entre
sí, y el `100` de WebDev y el `100` de General quieren decir lo mismo: el mejor de esa
categoría.

### Buenas ofertas

Modelos donde OpenCode los cobra más baratos que el precio público de referencia. El
ahorro se calcula como (precio AA − precio OpenCode) ÷ precio AA.

```text
                  Buenas ofertas Go (vs precio AA)
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Modelo              ┃ Precio AA $/1M ┃ Precio Go $/1M ┃ Ahorro % ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ longcat-2.0         │           $1.3 │           $0.5 │      60% │
│ deepseek-v4.1-flash │           $0.5 │           $0.3 │      50% │
│ deepseek-v4-pro     │           $2.0 │           $1.0 │      50% │
└─────────────────────┴────────────────┴────────────────┴──────────┘
```

El precio AA se calcula como blended 3:1 a partir del precio de input y output que publica
la API, que ya no lo da masticado.

### JSON

```json
{
  "source": "https://artificialanalysis.ai/",
  "generated_at": "2026-11-01T11:33:45.515720+00:00",
  "intelligence_index_version": 5,
  "opencode_url": "https://opencode.ai/inference/go/v1/models",
  "arena": {
    "source": "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset",
    "license": "CC-BY-4.0",
    "boards": [
      "text",
      "webdev",
      "agent"
    ],
    "published_at": "2026-10-28",
    "available": [
      "text",
      "webdev",
      "agent"
    ]
  },
  "models": [
    {
      "opencode_id": "mimo-v2.6-pro",
      "matched": true,
      "name": "MiMo-V2.6-Pro",
      "slug": "mimo-v2-6-pro",
      "creator": "Xiaomi",
      "intelligence_index": 29.9,
      "coding_index": null,
      "output_tokens_per_second": 46.95,
      "time_to_first_token_seconds": 3.03,
      "price_blended_1m": 0.54375,
      "price_input_1m": 0.435,
      "price_output_1m": 0.87,
      "arena_text": 1491.3511193426757,
      "arena_text_name": "MiMo-V2.6-Pro",
      "arena_webdev": 1625.417548626546,
      "arena_webdev_name": "MiMo-V2.6-Pro",
      "arena_agent": 0.027705996772957868,
      "arena_agent_name": "MiMo-V2.6-Pro",
      "arena_webdev_rank": 25,
      "multimodal": true,
      "go_price_blended_1m": 0.54375,
      "go_price_input_1m": 0.435,
      "go_price_output_1m": 0.87
    }
  ]
}
```

`intelligence_index_version` es la versión mayor del índice con la que se calcularon las
puntuaciones de esa ejecución. Los campos `price_*` son el precio público de Artificial
Analysis y los `go_price_*` el que cobra OpenCode. Los modelos sin datos en Artificial
Analysis aparecen con `opencode_id`, `matched: false`, sus campos `arena_*` y el precio de
OpenCode, sin las columnas de benchmarks.

`arena` describe la fuente: el dataset, la licencia, los tableros pedidos, la fecha de
publicación del leaderboard y los que respondieron. En cada modelo, `arena_text`,
`arena_webdev` y `arena_agent` son el valor de cada tablero (`null` si no hay fila) y
`arena_*_name` el nombre crudo que publica LMArena, guardado para poder auditar la
variante. `arena_webdev_rank` es el puesto en el tablero WebDev.

## Cómo funciona

1. Consulta el endpoint de modelos de OpenCode: `https://opencode.ai/inference/go/v1/models`
   para el catálogo Go (por defecto) o `https://opencode.ai/zen/v1/models` para Zen.
2. Consulta la API gratuita de Artificial Analysis
   (`/api/v2/language/models/free`), paginada de 200 en 200: 4 peticiones por ejecución de
   las 100 diarias que da el plan Free.
3. Consulta los tres tableros de LMArena (`text`, `webdev` y `agent`) en
   `https://datasets-server.huggingface.co/rows`, de 100 filas en 100. Las filas vienen
   agrupadas por categoría y solo se usan las de `overall`, así que la paginación se corta
   cuando una página deja de traer filas de esa categoría; hay un tope de 30 páginas por
   tablero. Son 10 peticiones medidas (text 6, webdev 3, agent 1), 628 filas `overall` y
   unos 4,6 s. `/filter` y `/search` del datasets-server no se usan: piden autenticación y
   devuelven error.
4. Empareja cada modelo de OpenCode con su entrada en Artificial Analysis: slug exacto,
   luego la subcadena más corta y por último el conjunto de tokens idéntico. Para Arena el
   emparejamiento es por tokens, sin subcadenas, para no confundir `glm-5.3` con
   `glm-5.3-flash`.
5. Añade el precio de OpenCode, leído de [models.dev](https://models.dev) y convertido a
   precio blended 3:1 por millón de tokens.
6. Muestra la tabla principal, la de Arena, el ranking calidad/precio y las mayores
   diferencias de precio.

## Limitaciones

- **El emparejamiento es heurístico**, no hay tabla de equivalencias escrita a mano. Un
  modelo mal emparejado da números creíbles y equivocados, así que conviene mirar la fila
  cuando aparece un modelo nuevo en el catálogo.
- **La cobertura de Arena es parcial.** 24 de los 28 modelos del catálogo Go tienen al
  menos un tablero (text 20, webdev 23, agent 22). `longcat-2.0`, `beam-free`,
  `qwen3.8-flash` e `iceman-contributor-free` no están en ninguno. La paginación se corta
  al salir de la categoría `overall`; si Hugging Face cambiara el orden de las filas, la
  cobertura podría bajar sin aviso.
- **El Elo no se compara entre tableros.** Cada tablero tiene su escala; un 1695 de
  `webdev` no es mejor que un 1465 de `text` por 230 puntos. El `Agent score` tampoco se
  compara con un Elo.
- **`Agent score` no es un porcentaje.** Es un score centrado en 0, con un rango de −0,21
  a +0,21; un `+0.10` no es un 10% de nada.
- **Las variantes de esfuerzo pueden no ser el mismo checkpoint.** LMArena publica el mismo
  modelo como `(Max)`, `(High)` o `(xHigh)`, y el emparejamiento se queda el de mayor
  valor, que no tiene por qué ser el que sirve OpenCode. El nombre crudo queda en el JSON
  (`arena_*_name`) para poder comprobarlo.
- **Si Hugging Face falla, el informe sale sin Arena.** Cada tablero se pide por separado:
  si uno no responde se avisa por stderr y se pierde esa columna, no el informe entero. Si
  fallan los tres, quedan las tablas de Artificial Analysis.
- **Los TTFT hay que leerlos con pinzas.** Algunos modelos salen con tiempos de primer
  token de cientos de segundos, que son artefactos del momento de la medición (colas, rate
  limits) y no latencia real.
- **Ojo con las versiones del índice.** El Intelligence Index cambia de versión mayor cada
  pocos meses y las notas dejan de ser comparables entre versiones. El pie de la tabla
  indica la versión con la que se generó la salida; no compares capturas antiguas.
- **No hay histórico.** Cada ejecución es una foto del momento.
- **No comprueba disponibilidad.** Si un modelo está de baja, no se entera.
- El precio por millón de tokens es una referencia de catálogo, no tu factura.

## Atribución

El uso de la API gratuita de Artificial Analysis requiere atribución a
https://artificialanalysis.ai/. Los precios de OpenCode provienen de https://models.dev/.

Los datos de Arena provienen de [LMArena](https://lmarena.ai), a través del dataset
[`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset),
publicado bajo **CC-BY-4.0**. La licencia exige atribución: si reutilizas esta salida, cita
LMArena y el dataset.
