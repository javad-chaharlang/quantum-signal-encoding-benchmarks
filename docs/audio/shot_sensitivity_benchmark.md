# Shot-Sensitivity Benchmark for Basis-Encoded Quantum Audio

## Objective

This experiment determines how finite measurement shots affect complete signal
reconstruction under an ideal noiseless model.

## Why coverage determines reconstruction

The encoded state has the form:

```math
|A\rangle =
\frac{1}{\sqrt{N}}
\sum_{t=0}^{N-1}
|a_t\rangle_{\mathrm{amp}}
|t\rangle_{\mathrm{time}}.
```

Every time index therefore has probability `1/N`. The amplitude associated with an
observed time index is a deterministic computational-basis value. Under ideal
measurement, the amplitude is not estimated from a continuous probability; it is
read from the observed basis state.

Consequently:

```text
exact reconstruction ⇔ every time index is observed at least once
```

The experiment is therefore connected to the classical coupon-collector coverage
problem.

## Experimental design

Signal lengths:

```text
4, 8, 16, 32 samples
```

Shot counts:

```text
4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096
```

For every signal-length and shot-count pair, 50 deterministic Monte Carlo seeds are
used.

## Reported metrics

- full exact-reconstruction rate;
- Wilson 95% interval for the empirical rate;
- exact theoretical full-coverage probability;
- observed-index coverage fraction;
- number of missing time indices;
- total variation distance from the uniform time distribution;
- coefficient of variation of per-index counts;
- theoretical shots required for 95% and 99% full coverage.

## Two-layer validation

The main grid samples from the exact ideal uniform time marginal using a multinomial
distribution. This avoids repeatedly simulating a deep state-preparation circuit
when the scientific variable is only finite-shot sampling.

Representative cases are also executed through the actual Qiskit pipeline:

```text
build circuit → Aer measurement → decode counts → reconstruct signal
```

This confirms that the analytical sampling model matches the implemented encoding
and decoding behavior.

## Run

```bash
python benchmarks/audio/run_basis_shot_sensitivity.py
```

## Expected outputs

```text
results/audio/shot_sensitivity/
├── README.md
├── shot_sensitivity.json
├── shot_sensitivity_runs.csv
└── shot_sensitivity_summary.csv

figures/audio/shot_sensitivity/
├── exact_reconstruction_probability.png
├── mean_missing_time_indices.png
├── mean_time_index_coverage.png
└── time_distribution_tvd.png
```

## Interpretation boundary

This benchmark measures finite-shot sensitivity only. It does not include gate
noise, readout noise, connectivity constraints, calibration drift, or real hardware.
Those effects belong to the separate noise-sensitivity experiment.
