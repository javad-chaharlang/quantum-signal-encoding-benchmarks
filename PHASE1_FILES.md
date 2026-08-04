# Phase 1 Placement Guide

Copy the following new files into the repository without deleting existing files:

```text
src/qseb/benchmarks/__init__.py
src/qseb/benchmarks/resource_scaling.py
benchmarks/audio/run_basis_resource_scaling.py
tests/benchmarks/test_resource_scaling.py
docs/audio/resource_scaling_benchmark.md
```

Then run:

```bash
ruff check .
ruff format --check .
pytest
python benchmarks/audio/run_basis_resource_scaling.py
```

Do not commit generated results yet. Review the real CSV, JSON, Markdown report, and
figures first. The next phase will whitelist selected outputs in `.gitignore` and
update the main README using the actual measured values.
