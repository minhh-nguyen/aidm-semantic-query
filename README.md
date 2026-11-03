# AIDM Semantic Queries

This repository is the 2nd part of the AIDM course at TU Darmstadt. It contains ...

The implementation is benchmarked against SemBench

## Requirements

SemBench
```bash
git submodule update --init --recursive
```

## Setup

```bash
uv sync                    # create .venv and install the package + dev deps
cp .env.example .env       # then set AIDM_USER (secret from Moodle)
```

`AIDM_USER` is required by the API proxy; `.env` is loaded explicitly with
`--env-file .env` so nothing leaks into the repository.

## Usage

```bash
uv run aidm-semantic-query                      # console script -> main()
uv run python -m aidm_semantic_query            # same, via the module
uv run --env-file .env python -m aidm_semantic_query.how_to_use_api_proxy
```

The API demo makes real requests (budget check, chat completions, embeddings)
and caches responses in `src/aidm_semantic_query/openai_cache/` (git-ignored).

## Tests

```bash
uv run pytest
```

## Layout

```
src/aidm_semantic_query/   # importable package (shipped in the wheel)
    __init__.py            # main() entry point
    __main__.py            # python -m aidm_semantic_query
    config.py              # env/config handling
    utils/                 # shared helpers (subpackage)
tests/                     # pytest suite
scripts/                   # one-off runnable utilities (not imported)
examples/                  # demos and experiments (not shipped)
```

Anything that must be imported belongs inside `src/aidm_semantic_query/`;
runnable-only code belongs in `scripts/` or `examples/`.
