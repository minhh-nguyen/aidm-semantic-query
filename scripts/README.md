# Scripts

One-off, runnable utilities that are **not** imported by the package: data
migrations, benchmarks, index rebuilds, ad-hoc experiments.

Run them with:

```bash
uv run python scripts/<script>.py
```

Keep importable business logic in `src/aidm_semantic_query/` and make scripts
thin wrappers around it.
