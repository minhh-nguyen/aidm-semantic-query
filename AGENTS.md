# AIDM Semantic Queries

Python semantic querry engine for interacting with the AI Dungeon Master API. Benchmark tested against SemBench VLDB 2026.
The exercise is written in the @part-2-instructions.pdf file. The code is in the `src/aidm_semantic_query` package, and the tests are in the `tests/` directory. The package is built with `uv` and can be run with `uv run aidm-semantic-query`.

## Dev environment

```bash
uv sync                    # install in .venv + dev deps
cp .env.example .env       # set AIDM_USER (required)
source .venv/bin/activate  # optional shell activation
```

`pythonversion: 3.15`. `pyproject.toml` uses `[project.scripts]` entrypoint pattern; package installs via uv build backend. SemBench is a git submodule—initialize with `git submodule update --init --recursive`.

## Build & test

```bash
uv run aidm-semantic-query                # runs src/aidm_semantic_query/main.py
uv run pytest                      # tests/ directory (configured in tool.pytest.ini_options)
```

Lint/format: ruff check/format (config file does not exist). Tests depend on `AIDM_USER` env var.

## Package layout

```
src/aidm_semantic_query/    # importable package shipped in wheel
  __init__.py               # main() entry point; module API here
  config.py                 # env/config handling
  how_to_use_api_proxy.py   # standalone script (uses --env-file .env)
  utils/                    # text utilities (empty placeholder)
```

`tests/`: pytest suite. `scripts/`: runnable-only utilities (not imported). `examples/`: demos/experiments (not shipped).

## Conventions

- Module entry point: `src/aidm_semantic_query/main.py`
- API proxy script invoked as `python -m aidm_semantic_query.how_to_use_api_proxy`
- Caches from how_to_use_api_proxy.go to openai_cache/ (gitignored)

## Pitfalls

- `AIDM_USER` mandatory; set by copying `.env.example .env` before running API proxy.
- SemBench submodule must be initialized explicitly; git clone alone may skip it.
- `openai_cache/` is gitignored but populated during demo runs—edit files there at your own risk.
