# Controlled Resource-Scaling Benchmark

## Why the first exploratory run was revised

The first run used one random signal for each benchmark point. This was useful for
verifying the pipeline, but it did not isolate amplitude-register width from input
bit density. In the amplitude-resolution study, the total number of set amplitude
bits varied between cases, producing non-monotonic resource curves.

The revised benchmark controls this effect with three profiles:

- **Sparse:** one set amplitude bit per sample.
- **Random:** five reproducible random signals summarized by mean and standard
  deviation.
- **Dense:** all amplitude bits set, representing the maximum loading density.

## Study A: signal-length scaling

The number of samples is varied over:

```text
2, 4, 8, 16, 32
```

The amplitude register is fixed at four qubits.

## Study B: amplitude-resolution scaling

The amplitude-register width is varied over:

```text
2, 3, 4, 5, 6, 7, 8 qubits
```

The signal length is fixed at eight samples.

## Reproducibility controls

- Random seeds: `42`, `52`, `62`, `72`, `82`
- Transpiler seed: `42`
- Transpiler optimization level: `1`
- Basis gates: `rz`, `sx`, `x`, `cx`
- Three timing repetitions per run; median reported
- One warm-up transpilation before timing
- Barriers disabled during resource measurement
- No statevector or shot-based simulation

## Run

```bash
python benchmarks/audio/run_basis_resource_scaling.py
```

## Generated outputs

```text
results/audio/resource_scaling/
├── README.md
├── resource_scaling.json
├── resource_scaling_runs.csv
└── resource_scaling_summary.csv

figures/audio/resource_scaling/
├── amplitude_depth_overhead_profiles.png
├── amplitude_transpiled_cx_profiles.png
├── amplitude_transpiled_depth_profiles.png
├── length_depth_overhead_profiles.png
├── length_transpiled_cx_profiles.png
└── length_transpiled_depth_profiles.png
```

## Interpretation boundary

The benchmark characterizes the present explicit data-loading implementation. It
does not prove quantum advantage, optimal state preparation, hardware feasibility,
or execution fidelity.

## Results interpretation

See [`resource_scaling_results.md`](resource_scaling_results.md) for the controlled numerical analysis.
