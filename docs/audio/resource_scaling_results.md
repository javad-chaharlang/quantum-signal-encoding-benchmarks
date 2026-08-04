# Controlled Resource-Scaling Results

## Experimental scope

The controlled benchmark evaluates the current basis-encoded quantum-audio
state-preparation circuit under two studies:

1. signal length from 2 to 32 samples with four amplitude qubits; and
2. amplitude-register width from 2 to 8 qubits with eight samples.

Three loading profiles are used:

- **Sparse:** one set amplitude bit per sample;
- **Random:** five deterministic seeds, summarized by mean and standard deviation;
- **Dense:** all amplitude bits set.

The transpiler uses seed 42, optimization level 1, and the basis
`rz`, `sx`, `x`, and `cx`. Barriers are disabled. The benchmark measures circuit
construction and transpilation only; it does not perform statevector, shot-based,
noisy, or hardware execution.

Local execution environment:

- Python 3.14.6
- Qiskit 2.5.1
- Qiskit Aer 0.17.2
- NumPy 2.5.1
- Matplotlib 3.11.1

## Result 1: signal length dominates resource growth

For the random profile, increasing signal length from 2 to 32 samples changed:

| Metric | 2 samples | 32 samples | Growth |
|---|---:|---:|---:|
| Total qubits | 5 | 9 | 1.8x |
| Mean transpiled depth | 6.8 | 5759.0 | 846.9x |
| Mean transpiled size | 6.8 | 6596.6 | 970.1x |
| Mean CX count | 3.0 | 2228.4 | 742.8x |
| Mean depth overhead | 1.12x | 45.52x | 40.5x |

At 32 samples, profile-dependent values were:

| Profile | Transpiled depth | CX count | Depth overhead |
|:---|---:|---:|---:|
| Sparse | 2711 | 1058 | 29.8x |
| Random | 5759.0 ± 387.5 | 2228.4 ± 148.8 | 45.5 ± 1.7x |
| Dense | 11110 | 4322 | 59.4x |

An empirical log-log fit across the tested signal lengths gives an approximate
transpiled-depth exponent between 2.2 and 2.4, depending on the profile. This is a
description of the observed finite range, not a proof of asymptotic complexity.

## Result 2: amplitude width and bit density are separate factors

With eight samples, dense loading produced exactly linear growth over two to eight
amplitude qubits:

- transpiled depth increased by 206 per added amplitude qubit;
- transpiled size increased by 238 operations per added amplitude qubit;
- CX count increased by 110 per added amplitude qubit.

Dense-profile values changed from:

| Metric | 2 amplitude bits | 8 amplitude bits |
|---|---:|---:|
| Total qubits | 5 | 11 |
| Transpiled depth | 427 | 1663 |
| Transpiled size | 495 | 1923 |
| CX count | 222 | 882 |

The sparse profile maintained exactly eight loaded amplitude bits across all widths.
Its transpiled depth changed only from 218 to 203, a difference of -6.9%. The small
decrease is attributable to transpiler optimization and circuit arrangement rather
than a reduction in the number of data-loading operations.

The random profile increased from 209.8 ± 60.5 to 646.6 ± 140.2 in transpiled
depth. Across all amplitude-resolution runs, the Pearson correlation between total
amplitude-bit Hamming weight and transpiled depth was approximately 0.978.

## Interpretation

The benchmark supports four conclusions:

1. **Qubit count alone is not a sufficient cost indicator.**
2. **Longer signal indices increase both the number and control width of loading
   operations.**
3. **Amplitude resolution creates additional cost only when the extra amplitude
   bits are actually loaded.**
4. **Decomposition of multi-controlled operations into the selected basis becomes
   the dominant resource cost for longer signals.**

These results characterize the present explicit state-preparation implementation.
They do not establish quantum advantage, hardware feasibility, execution fidelity,
or asymptotic optimality.

## Reproducible artifacts

- `benchmarks/audio/run_basis_resource_scaling.py`
- `src/qseb/benchmarks/resource_scaling.py`
- `results/audio/resource_scaling/resource_scaling_runs.csv`
- `results/audio/resource_scaling/resource_scaling_summary.csv`
- `results/audio/resource_scaling/resource_scaling.json`
- `results/audio/resource_scaling/README.md`
