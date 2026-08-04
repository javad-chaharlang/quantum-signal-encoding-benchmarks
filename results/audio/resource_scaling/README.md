# Controlled Resource Scaling: Basis-Encoded Quantum Audio

## Purpose

This benchmark measures how the current explicit state-preparation circuit scales
with signal length, amplitude-register width, and amplitude-bit density.

## Controlled design

Three input profiles are evaluated:

- **Sparse:** one set amplitude bit per sample.
- **Random:** uniform random amplitudes aggregated across five fixed seeds.
- **Dense:** all amplitude bits set for every sample.

Configuration:

- Random seeds: `[42, 52, 62, 72, 82]`
- Transpiler seed: `42`
- Optimization level: `1`
- Timing repeats: `3`; the median is reported per run
- Basis gates: `['rz', 'sx', 'x', 'cx']`
- Barriers disabled during resource measurement
- No statevector, shot-based, noisy, or hardware execution

## Key findings from this run

1. **Signal length is the dominant scaling pressure.** For the random profile,
   increasing the signal from `2` to `32`
   samples increased mean transpiled depth by `846.9x` and
   mean CX count by `742.8x`, while total qubits increased only
   from `5` to
   `9`.
2. **Transpilation overhead becomes dominant at longer signals.** At
   `32` samples, the random profile reached a mean depth
   overhead of `45.5x`.
3. **Amplitude width alone is not the full cost driver.** Under the dense
   profile, each additional amplitude qubit added exactly
   `206` layers of transpiled depth and
   `110` CX gates across the tested range.
4. **Fixed loading sparsity keeps cost nearly constant.** The sparse
   amplitude-resolution profile held the number of loaded amplitude bits fixed,
   and transpiled depth changed by only `-6.9%` from
   `2` to `8` amplitude qubits.

The central conclusion is that state-preparation cost is jointly controlled by
the width of the time-register controls and the number of set amplitude bits.
Qubit count alone is therefore not a sufficient resource indicator.

## Study A: signal-length scaling

| Samples | Profile | Runs | Qubits | Hamming weight | Transpiled depth | Transpiled size | CX count | Depth overhead |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 2 | sparse | 1 | 5 | 2.0 | 6.0 | 6.0 | 2.0 | 1.2 |
| 2 | random | 5 | 5 | 3.0 ± 1.2 | 6.8 ± 1.6 | 6.8 ± 1.6 | 3.0 ± 1.2 | 1.1 ± 0.1 |
| 2 | dense | 1 | 5 | 8.0 | 12.0 | 12.0 | 8.0 | 1.1 |
| 4 | sparse | 1 | 6 | 4.0 | 44.0 | 82.0 | 24.0 | 4.4 |
| 4 | random | 5 | 6 | 8.2 ± 2.5 | 86.4 ± 24.5 | 136.2 ± 32.4 | 49.2 ± 14.9 | 6.0 ± 0.6 |
| 4 | dense | 1 | 6 | 16.0 | 164.0 | 238.0 | 96.0 | 7.5 |
| 8 | sparse | 1 | 7 | 8.0 | 213.0 | 275.0 | 106.0 | 10.1 |
| 8 | random | 5 | 7 | 16.8 ± 1.9 | 393.0 ± 42.2 | 481.4 ± 46.8 | 202.4 ± 23.0 | 13.2 ± 0.9 |
| 8 | dense | 1 | 7 | 32.0 | 839.0 | 971.0 | 442.0 | 18.6 |
| 16 | sparse | 1 | 8 | 16.0 | 977.0 | 1180.0 | 392.0 | 22.2 |
| 16 | random | 5 | 8 | 34.6 ± 5.3 | 2029.8 ± 338.7 | 2418.0 ± 392.8 | 834.8 ± 139.7 | 32.2 ± 2.7 |
| 16 | dense | 1 | 8 | 64.0 | 4096.0 | 4756.0 | 1640.0 | 44.5 |
| 32 | sparse | 1 | 9 | 32.0 | 2711.0 | 3203.0 | 1058.0 | 29.8 |
| 32 | random | 5 | 9 | 67.4 ± 4.1 | 5759.0 ± 387.5 | 6596.6 ± 426.9 | 2228.4 ± 148.8 | 45.5 ± 1.7 |
| 32 | dense | 1 | 9 | 128.0 | 11110.0 | 12779.0 | 4322.0 | 59.4 |

![Transpiled depth versus signal length][length-depth]

![CX count versus signal length][length-cx]

![Depth overhead versus signal length][length-overhead]

## Study B: amplitude-resolution scaling

| Amplitude bits | Profile | Runs | Qubits | Hamming weight | Transpiled depth | Transpiled size | CX count | Depth overhead |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 2 | sparse | 1 | 5 | 8.0 | 218.0 | 263.0 | 110.0 | 10.4 |
| 2 | random | 5 | 5 | 8.0 ± 2.2 | 209.8 ± 60.5 | 257.0 ± 66.2 | 104.8 ± 32.7 | 9.8 ± 1.9 |
| 2 | dense | 1 | 5 | 16.0 | 427.0 | 495.0 | 222.0 | 14.7 |
| 3 | sparse | 1 | 6 | 8.0 | 216.0 | 269.0 | 108.0 | 10.3 |
| 3 | random | 5 | 6 | 14.6 ± 3.0 | 377.0 ± 81.3 | 448.8 ± 90.7 | 195.2 ± 42.7 | 13.5 ± 1.6 |
| 3 | dense | 1 | 6 | 24.0 | 633.0 | 733.0 | 332.0 | 17.1 |
| 4 | sparse | 1 | 7 | 8.0 | 213.0 | 275.0 | 106.0 | 10.1 |
| 4 | random | 5 | 7 | 16.8 ± 1.9 | 393.0 ± 42.2 | 481.4 ± 46.8 | 202.4 ± 23.0 | 13.2 ± 0.9 |
| 4 | dense | 1 | 7 | 32.0 | 839.0 | 971.0 | 442.0 | 18.6 |
| 5 | sparse | 1 | 8 | 8.0 | 211.0 | 281.0 | 104.0 | 10.0 |
| 5 | random | 5 | 8 | 21.4 ± 3.0 | 490.0 ± 55.9 | 598.4 ± 67.1 | 255.6 ± 29.6 | 14.2 ± 0.9 |
| 5 | dense | 1 | 8 | 40.0 | 1045.0 | 1209.0 | 552.0 | 19.7 |
| 6 | sparse | 1 | 9 | 8.0 | 208.0 | 287.0 | 102.0 | 9.9 |
| 6 | random | 5 | 9 | 24.8 ± 1.6 | 512.2 ± 70.1 | 635.8 ± 71.8 | 269.6 ± 37.0 | 13.5 ± 1.7 |
| 6 | dense | 1 | 9 | 48.0 | 1251.0 | 1447.0 | 662.0 | 20.5 |
| 7 | sparse | 1 | 10 | 8.0 | 206.0 | 293.0 | 100.0 | 9.8 |
| 7 | random | 5 | 10 | 25.0 ± 3.4 | 516.4 ± 101.2 | 645.0 ± 108.0 | 272.8 ± 53.8 | 13.5 ± 1.9 |
| 7 | dense | 1 | 10 | 56.0 | 1457.0 | 1685.0 | 772.0 | 21.1 |
| 8 | sparse | 1 | 11 | 8.0 | 203.0 | 299.0 | 98.0 | 9.7 |
| 8 | random | 5 | 11 | 30.4 ± 6.8 | 646.6 ± 140.2 | 800.8 ± 158.1 | 341.2 ± 77.6 | 14.8 ± 1.1 |
| 8 | dense | 1 | 11 | 64.0 | 1663.0 | 1923.0 | 882.0 | 21.6 |

![Transpiled depth versus amplitude width][amplitude-depth]

![CX count versus amplitude width][amplitude-cx]

![Depth overhead versus amplitude width][amplitude-overhead]

## Interpretation boundary

The sparse and dense profiles expose lower- and upper-content-loading regimes, while
the random profile estimates typical variability. This prevents amplitude-register
width from being confused with a single signal's number of set bits.

These measurements characterize the present circuit construction and selected
transpiler configuration. They do not establish quantum advantage, hardware
feasibility, execution fidelity, or asymptotic optimality.

Machine-readable outputs:

- `results/audio/resource_scaling/resource_scaling_runs.csv`
- `results/audio/resource_scaling/resource_scaling_summary.csv`
- `results/audio/resource_scaling/resource_scaling.json`

[length-depth]: ../../../figures/audio/resource_scaling/length_transpiled_depth_profiles.png
[length-cx]: ../../../figures/audio/resource_scaling/length_transpiled_cx_profiles.png
[length-overhead]: ../../../figures/audio/resource_scaling/length_depth_overhead_profiles.png
[amplitude-depth]: ../../../figures/audio/resource_scaling/amplitude_transpiled_depth_profiles.png
[amplitude-cx]: ../../../figures/audio/resource_scaling/amplitude_transpiled_cx_profiles.png
[amplitude-overhead]: ../../../figures/audio/resource_scaling/amplitude_depth_overhead_profiles.png
