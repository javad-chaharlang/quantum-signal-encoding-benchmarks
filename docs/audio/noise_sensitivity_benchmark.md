# Controlled Noise-Sensitivity Benchmark

## Objective

This experiment measures how synthetic gate and readout errors affect the current
basis-encoded quantum audio representation.

## Noise families

Three controlled families are evaluated:

1. **Gate noise:** one-qubit and two-qubit depolarizing errors.
2. **Readout noise:** symmetric classical bit-flip error at measurement.
3. **Combined noise:** gate and readout errors applied together.

The ideal condition is repeated with the same simulator seeds to provide a finite-shot
reference.

## Gate mapping

The measured circuit is transpiled to:

```text
rz, sx, x, cx
```

The benchmark applies:

- one-qubit depolarizing error to `sx` and `x`;
- two-qubit depolarizing error to `cx`;
- no synthetic error to `rz`;
- symmetric readout error to every measured qubit.

## Severity grid

| Severity | One-qubit | Two-qubit | Readout |
|:---|---:|---:|---:|
| Low | 0.0005 | 0.005 | 0.005 |
| Moderate | 0.001 | 0.010 | 0.010 |
| High | 0.002 | 0.020 | 0.020 |
| Severe | 0.005 | 0.050 | 0.050 |

These are controlled stress-test values, not calibration data from a specific
physical backend.

## Experimental grid

- Signal lengths: `4`, `8`
- Amplitude width: `4` qubits
- Shots: `1024`
- Simulator seeds: `42`, `52`, `62`, `72`, `82`
- Conditions per signal length: `13`
- Total runs: `2 × 13 × 5 = 130`
- Aggregated conditions: `26`

## Metrics

- exact reconstruction rate;
- modal amplitude accuracy;
- normalized modal amplitude MAE;
- correct ideal-basis shot fraction;
- amplitude-register bit-error rate;
- joint-distribution total variation distance;
- time-marginal total variation distance;
- observed-index coverage;
- simulation time.

## Run

```bash
python benchmarks/audio/run_basis_noise_sensitivity.py
```

## Expected outputs

```text
results/audio/noise_sensitivity/
├── README.md
├── noise_sensitivity.json
├── noise_sensitivity_runs.csv
└── noise_sensitivity_summary.csv

figures/audio/noise_sensitivity/
├── amplitude_bit_error_rate.png
├── correct_basis_shot_fraction.png
├── exact_reconstruction_rate.png
├── joint_distribution_tvd.png
└── modal_amplitude_accuracy.png
```

## Interpretation boundary

This stage uses synthetic, independent error channels. It does not yet model a
specific backend, coupling map, gate durations, thermal relaxation, correlated
readout errors, crosstalk, leakage, calibration drift, or error mitigation.
