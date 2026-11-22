# AIDM Semantic Queries

Lab repository for **Part 2: System Implementation** of the AIDM course at
TU Darmstadt. The goal is to build a **general semantic query processing engine**
that executes [SemBench](https://sembench.github.io/SemBench/) queries with
LLM-backed semantic operators, then to improve the trade-off between result
quality, latency, and cost.

The repository is currently a **skeleton**: the package, the API plumbing, and
the module layout exist, but the operators, planner, and SQL front end are still
stubs. See [Current status](#current-status).


## Current status

| Area | State |
| --- | --- |
| Package + console script | Works, but `main()` only prints a greeting |
| API proxy reference script | Works; cached requests, 20-worker pool |
| `llm/client.py` | Partial `LLMClient`; `send_request()` is a placeholder |
| `sem_ops/*` | Stubs that print "not implemented yet" |
| `plan/*`, `sql/*`, `data/loader.py` | Empty placeholders |
| `functions/*` | Comments only |
| Tests | Collect 0 tests |

`pandas` and `duckdb` are **not** dependencies yet; add them to
`pyproject.toml` when the relational layer is implemented.


## Requirements and setup

- Python 3.15 (`uv` provisions it from `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Access to the TU Darmstadt API proxy from eduroam or VPN
- `AIDM_USER` secret from Moodle
- SemBench submodule

```bash
git submodule update --init --recursive
uv sync                    # create .venv and install the package + dev deps
cp .env.example .env       # fresh clone only; then set AIDM_USER
```

`AIDM_USER` is required by the API proxy. `.env` is loaded explicitly with
`--env-file .env`; it is git-ignored and must never be committed.

## Usage

```bash
uv run aidm-semantic-query                   # console script -> main()
uv run python -m aidm_semantic_query.main    # module shim
```

`python -m aidm_semantic_query` does **not** work yet: the package has no
`__main__.py`, even though `main.py`'s docstring claims it enables that command.
The console script currently only prints a greeting.

Run the course API demo (makes real requests and spends budget):

```bash
uv run --env-file .env python -m aidm_semantic_query.utils.how_to_use_api_proxy
```

It checks the remaining monthly budget, sends chat-completion and embedding
requests, and caches successful responses. The reference script caches next to
itself in `src/aidm_semantic_query/utils/openai_cache/` (git-ignored).
`config.CACHE_DIR` points at `src/aidm_semantic_query/openai_cache/` and is not
used by the reference script yet; pick one location before building the client
cache.

## API proxy and models

The proxy is OpenAI-compatible. Base URL:
`http://runner-aidm.dm.informatik.tu-darmstadt.de:8080`. Endpoints:
`/budget`, `/chat_completions`, `/embeddings`. The proxy allows at most **20
concurrent workers**.

| Model | Input USD / 1M | Cached input USD / 1M | Output USD / 1M |
| --- | ---: | ---: | ---: |
| `gpt-6-luna` | 0.10 | 0.01 | 0.50 |
| `gpt-6.1-terra` | 1.00 | 0.05 | 5.00 |
| `gpt-6.1-sol` | 2.00 | 0.10 | 10.00 |
| `text-embedding-3-small` | 0.02 | — | — |
| `text-embedding-3-large` | 0.13 | — | — |

These are the prices in the course reference script. Cache writes are billed at
1.25x the input price. Prompts above 272,000 tokens are billed at 2x input and
1.5x output. Local models (for example SBERT embeddings) are allowed.

Requests are cached by a SHA-256 hash of the request JSON, so identical requests
are free after the first call. Deleting the cache forces new paid requests.
Start with a small SemBench `scale_factor`, reuse the cache, and contact the
course staff if the monthly budget runs out.

## SemBench

SemBench is included as a pinned git submodule. Its README is the source of
truth for dataset setup, runner interfaces, and evaluation:

- Paper: <https://arxiv.org/abs/2511.01716>
- Website: <https://sembench.github.io/SemBench/>
- Repository: <https://github.com/SemBench/SemBench>

SemBench has its own isolated environments. Do **not** run it with this
project's `.venv` (it fails on missing `dotenv`); use its setup instead:

```bash
bash SemBench/scripts/setup_envs.sh
source SemBench/.venvs/sembench/bin/activate
```

`setup_envs.sh` installs the orchestrator and all supported systems; pass system
names (for example `bash SemBench/scripts/setup_envs.sh lotus palimpzest`) to
install a subset. SemBench downloads datasets on demand and builds the
multi-modal databases for the chosen scale factor. A typical run:

```bash
python3 SemBench/src/run.py \
  --systems lotus \
  --use-cases movie \
  --queries 1 3 \
  --model gemini-2.5-flash \
  --scale-factor 2000
```

Your own engine can reuse SemBench's data, queries, and evaluation logic without
using its runners.

### Query locations

Most scenarios store BigQuery-style queries under:

```text
SemBench/files/<scenario>/query/bigquery/Q*.sql
```

with `natural_language/` siblings, and `gold_sql/` where available (Movie,
Animals, Medical). **MMQA** has no `gold_sql/` directory; **Cars** has no `data/`
directory in this checkout.

E-Commerce is the exception: its queries are TOML files under
`SemBench/files/ecomm/queries/q*.toml`. Each has a `[metadata]` section
(`query_id`, `modalities`, `required_operators`, `description`), a `[definition]`
section (`natural_language`, `sql`, `ground_truth`, `accuracy_metric`), and
system-specific dialects under `queries/dialects/`. Its SQL uses
`SEM_FILTER('...', productDescriptors:description)` instead of `AI.IF(...)`.

Current counts in the submodule: Movie 10, Animals 10, MMQA 16, E-Commerce 14
TOML files, Cars 10, Medical 12.

The BigQuery files are **Jinja templates** with placeholders such as
`<<connection>>`, `<<query_id>>`, `<<thinking_budget>>`, and `<<other_params>>`
that the SemBench runner fills in. A custom engine must replace them or ignore
them consistently.

Example semantic filter (Movie Q1):

```sql
SELECT reviewId
FROM movie.reviews AS r
WHERE AI.IF(('Determine if the following movie review is clearly positive, review: ', r.reviewText))
LIMIT 5;
```

Example cross-modal filter (Animals Q10):

```sql
SELECT City AS city, StationID AS stationID
FROM animals_dataset.image_data_mm
WHERE AI.IF(('Does this image contain a zebra?', image))
GROUP BY city, stationID
ORDER BY COUNT(*) DESC
LIMIT 1;
```

`SemBench Queries.pdf` is a 4-page sample handout, not the full benchmark. It
walks through Movie Q1/Q3 and Animals Q1/Q10 (positive-review filtering,
counting, zebra-image counting, and grouping by city/station). The full query set
is in the submodule; the course query list is on Moodle.

## Project layout

```text
src/aidm_semantic_query/
    __init__.py              # main(); console-script entrypoint (greeting only)
    main.py                  # python -m aidm_semantic_query.main shim
    config.py                # AIDM_USER, CACHE_DIR, MissingUserError
    data/loader.py           # planned: SemBench files/<scenario>/data -> DuckDB
    functions/prompts.py     # planned: build messages, image base64 parts
    functions/tracker.py     # planned: tokens, cost, calls, latency per query
    llm/client.py            # partial LLMClient; cache/retry/pool planned
    llm/pricing.py           # planned: cost calculation and limits
    plan/node.py             # planned: Scan, Filter, SemFilter, SemMap, SemJoin,
                             #          Join, Aggregate, Sort, Limit, Project
    plan/executer.py         # planned: plan execution
    plan/optimizer.py        # planned: plan rewrites
    sem_ops/sem_filter.py    # stub
    sem_ops/sem_map.py       # stub
    sem_ops/sem_join.py      # stub
    sem_ops/sem_score.py     # stub (AI.SCORE / SEM_CLASSIFY)
    sql/parser.py            # planned: SQL front end
    sql/to_plan.py           # planned: SQL -> logical plan
    utils/how_to_use_api_proxy.py  # course reference; do not modify
    utils/text.py            # placeholder
tests/                       # pytest target; currently a placeholder
docs/                        # design notes (currently a placeholder)
scripts/                     # runnable-only utilities (not shipped)
examples/                    # demos and experiments (not shipped)
SemBench/                    # git submodule; do not edit
```

Importable logic belongs in `src/aidm_semantic_query/`. `scripts/` and
`examples/` are thin wrappers around it. `requirements.txt` is generated by
`uv export`; edit `pyproject.toml` and `uv.lock` instead. `papers/` is a local,
git-ignored reading list.

## Tests

```bash
uv run python -m pytest
```

Use `python -m pytest` rather than `uv run pytest`: the `.venv/bin/pytest`
shebang can point at an old checkout path and fail to spawn. `tests/test_smoke.py`
currently contains only a docstring, so the suite collects zero tests until tests
are added. If `uv` warns that `VIRTUAL_ENV` points to an old checkout, run
`unset VIRTUAL_ENV` or `source .venv/bin/activate`.

## Optimization directions

The course grades both execution and optimization. Useful starting points:

- **Operator-level:** batch prompts, cache repeated subexpressions, route easy
  predicates to `gpt-6-luna`, fuse compatible filters/maps, use lightweight proxy
  models or task cascades with verification.
- **Plan-level:** push relational filters before semantic operators, reorder
  joins, stop early for `LIMIT`/top-k, use cardinality and selectivity estimates,
  and approximate predicates with statistical guarantees.
- **Accuracy/cost trade-off:** measure per-query quality and money/latency, then
  plot the Pareto frontier instead of optimizing a single number.

The `papers/` directory (local only) groups relevant work into benchmarks,
operator-level optimizations, plan-level optimizations, and semantic query
processing engines (LOTUS, Palimpzest, ThalamusDB, and others).

## Known gaps to fix

- `LLMClient` defaults to `gpt-6.1-luna`, which is **not** a valid proxy model;
  use `gpt-6-luna`.
- `python -m aidm_semantic_query` fails because `__main__.py` is missing, while
  `main.py` claims to support it.
- `examples/README.md` still points at the old
  `src/aidm_semantic_query/how_to_use_api_proxy.py` path.
- The two cache locations (`config.CACHE_DIR` vs. the reference script's
  `utils/openai_cache/`) are not unified.
- `pandas`/`duckdb` are not declared as dependencies yet.

See `part-2-instructions.pdf` for the full task description and
`SemBench Queries.pdf` for sample queries.
