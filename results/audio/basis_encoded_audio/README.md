# Basis-Encoded Quantum Audio: Reproducible Experiment

## Configuration

| Item | Value |
|---|---:|
| Input samples | `[3, 6, 2, 5]` |
| Amplitude qubits | 3 |
| Time qubits | 2 |
| Total qubits | 5 |
| Shots | 4096 |
| Simulator seed | 42 |
| Transpiler optimization level | 1 |

## Reconstruction

- Original: `[3, 6, 2, 5]`
- Reconstructed: `[3, 6, 2, 5]`
- Exact reconstruction: **True**

![Original and reconstructed samples](../../../figures/audio/basis_encoded_audio/reconstruction.png)

## Circuit

![Basis-encoded audio circuit](../../../figures/audio/basis_encoded_audio/circuit.png)

## Measurement distribution

![Measurement counts](../../../figures/audio/basis_encoded_audio/measurement_counts.png)

## Resource metrics

| Metric | Value |
|---|---:|
| Raw depth | 13 |
| Raw size | 17 |
| Transpiled depth | 77 |
| Transpiled size | 118 |

The complete machine-readable report is available in
`results/audio/basis_encoded_audio/experiment_report.json`.

## Interpretation

This experiment verifies that the small unsigned integer signal is encoded into
time-indexed computational-basis amplitudes and reconstructed exactly under ideal
shot-based simulation. It is a transparent baseline rather than a claim of quantum
advantage. The next benchmark should study scaling, finite-shot coverage, and noise.
