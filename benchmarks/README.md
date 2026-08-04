# Benchmarks

Benchmark scripts will be organized by research question rather than by plotting convenience.

Planned suites:

- `resource_scaling/` — qubits, depth, gate counts, runtime, and memory
- `shot_sensitivity/` — time-index coverage and reconstruction versus shots
- `noise_sensitivity/` — depolarizing, readout, and backend-derived noise models
- `cross_method/` — controlled comparison of audio and image representations

Each benchmark must follow [`docs/benchmark_protocol.md`](../docs/benchmark_protocol.md) and write machine-readable results to `results/`.
