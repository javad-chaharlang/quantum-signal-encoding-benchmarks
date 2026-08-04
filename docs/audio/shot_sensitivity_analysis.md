# Shot-Sensitivity Analysis: Basis-Encoded Quantum Audio

## Execution summary

- Raw Monte Carlo runs: **2200**
- Aggregated conditions: **44**
- Monte Carlo seeds per condition: **50**
- Signal lengths: `[4, 8, 16, 32]`
- Shot counts: `[4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]`
- Qiskit Aer validation cases: **2**
- Noise model: **None**
- Hardware execution: **False**

## Theoretical full-coverage thresholds

| Samples | Shots for ≥95% exact reconstruction | Shots for ≥99% exact reconstruction |
|---:|---:|---:|
| 4 | 16 | 21 |
| 8 | 38 | 51 |
| 16 | 90 | 115 |
| 32 | 203 | 255 |

The required number of shots grows faster than linearly with signal length and is
consistent with coupon-collector behavior: approximately `N log N` measurements are
needed to observe all `N` uniformly probable time indices with high confidence.

## Agreement between theory and Monte Carlo results

The exact theoretical full-coverage probability fell inside the empirical Wilson
95% confidence interval for **44 of
44 conditions**.

The maximum absolute difference between the empirical exact-reconstruction rate and
the theoretical probability was **0.1171**,
observed for:

- Samples: `4`
- Shots: `8`
- Empirical rate: `0.7400`
- Theoretical rate: `0.6229`

This difference remains compatible with the 50-run Monte Carlo uncertainty because
the theoretical value lies inside the corresponding Wilson interval.

The maximum absolute error between empirical and theoretical mean coverage was only
**0.0301**.

## Representative operating points

| Samples | Shots | Empirical exact rate | Theory | Mean coverage | Mean missing |
|---:|---:|---:|---:|---:|---:|
| 4 | 16 | 0.9600 | 0.9600 | 0.9900 | 0.040 |
| 8 | 32 | 0.8800 | 0.8913 | 0.9850 | 0.120 |
| 16 | 64 | 0.8200 | 0.7652 | 0.9875 | 0.200 |
| 32 | 128 | 0.6200 | 0.5629 | 0.9844 | 0.500 |

These points illustrate the transition region: mean index coverage can already be
high while exact reconstruction is still substantially below one, because a single
missing time index is sufficient to make the reconstructed signal incomplete.

## Actual Qiskit validation

| Samples | Shots | Coverage | Observed amplitudes correct | Exact reconstruction |
|---:|---:|---:|:---:|:---:|
| 4 | 256 | 1.0000 | True | True |
| 8 | 1024 | 1.0000 | True | True |

Both validation cases confirmed that every observed time index carries its correct
basis-encoded amplitude and that full index coverage produces exact signal
reconstruction.

## Distribution convergence

The total variation distance between the empirical time-index distribution and the
uniform target decreased consistently as the number of shots increased. At 4096
shots, the mean TVD values were:

| Samples | Mean TVD |
|---:|---:|
| 4 | 0.0102 |
| 8 | 0.0164 |
| 16 | 0.0243 |
| 32 | 0.0345 |

Larger signals require more shots to achieve the same distributional precision
because each individual time index receives fewer expected observations.

## Main conclusion

For this ideal basis-encoded representation, finite-shot reconstruction is governed
primarily by **time-index coverage**, not by amplitude estimation error. Once a time
index is observed, its amplitude is deterministic. The practical ideal-simulation
rule is therefore:

> Choose shots from the desired full-coverage probability and signal length, rather
> than using one fixed shot count for every signal size.

## Interpretation boundary

These findings isolate sampling uncertainty only. Gate noise, readout noise,
transpiler topology, calibration drift, and real-hardware behavior are not included.
Those effects belong to the next noise-sensitivity experiment.
