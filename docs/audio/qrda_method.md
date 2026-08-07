# QRDA method and implementation scope

## Primary reference

Wang, J. (2016). QRDA: Quantum Representation of Digital Audio. *International Journal of Theoretical Physics, 55*, 1622-1641. https://doi.org/10.1007/s10773-015-2800-2

## Representation

For an effective digital-audio signal containing \(L\) samples, QRDA uses an amplitude register of \(m\) qubits and a time register of \(l\) qubits, where

```math
l=
\begin{cases}
\lceil \log_2 L\rceil, & L>1,\\
1, & L=1.
\end{cases}
```

The complete QRDA box contains \(2^l\) time positions:

```math
\left|B\right\rangle
=
\frac{1}{\sqrt{2^l}}
\left(
\sum_{t=0}^{L-1}
\left|S_t\right\rangle_{\mathrm{amp}}
\otimes
\left|t\right\rangle_{\mathrm{time}}
+
\sum_{t=L}^{2^l-1}
\left|0\right\rangle^{\otimes m}_{\mathrm{amp}}
\otimes
\left|t\right\rangle_{\mathrm{time}}
\right).
```

The first summation contains effective audio samples. The second contains redundant QRDA box positions whenever \(L\) is not a power of two.

The implementation exposes `num_samples`, `time_bits`, `box_size`, `padding_count`, and `padding_fraction`.

## Unsigned amplitudes

The quantum encoder accepts

```math
0 \leq S_t \leq 2^m-1.
```

## Signed digital-audio preprocessing

For an \(m\)-bit signed sample

```math
-2^{m-1}\leq x_t\leq 2^{m-1}-1,
```

the repository provides

```math
S_t=x_t+2^{m-1},
```

through `signed_to_unsigned_samples()`, and

```math
x_t=S_t-2^{m-1}
```

through `unsigned_to_signed_samples()`.

The QRDA encoder remains unsigned; translation is explicit preprocessing/postprocessing.

## Preparation protocol

### Step 1 — Blank QRDA box

The primary paper defines

```math
U_1=I^{\otimes m}\otimes H^{\otimes l}.
```

The repository omits explicit identity gates and applies Hadamard gates to the time register.

### Step 2 — Conditional amplitude loading

Every set amplitude bit is written conditionally on its time basis state with a logical `mcx`.

Zero-valued controls are implemented through `X` conjugation around `mcx`.

Redundant positions receive no amplitude writes and therefore remain at amplitude zero.

## Qiskit register convention

The amplitude register precedes the time register. For amplitude width \(m\),

```math
\mathrm{basis\ index}=S_t+(t\ll m).
```

## Primary-paper worked example

Signed samples:

```text
[0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0]
```

Unsigned QRDA amplitudes:

```text
[8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8]
```

Validated properties:

| Property | Value |
|---|---:|
| Effective samples | 15 |
| Amplitude qubits | 4 |
| Time qubits | 4 |
| Total qubits | 8 |
| Box size | 16 |
| Padding count | 1 |
| Padding state | \(T=15,\ S_T=0\) |
| Nonzero basis states | 16 |
| Probability per state | 1/16 |
| Statevector amplitude magnitude | 1/4 |
| State fidelity to independent reference | 1.0 |
| Logical controlled amplitude writes | 33 |
| Qiskit logical `mcx` writes | 33 |
| Zero-control `X` wrappers | 64 |

## Equivalence levels

### State equivalence

The independently constructed reference state and the prepared Qiskit state have fidelity 1 within numerical tolerance.

### Logical preparation equivalence

The repository reproduces the paper's four Hadamard operations and 33 controlled amplitude writes.

### Physical gate decomposition

Physical gate-for-gate identity is not claimed. Qiskit decomposes `mcx` according to the software stack, basis gates, optimization level, and transpiler seed.

The paper's symbolic 33 four-controlled writes must therefore not be identified with the final transpiled CX count.

## Measurement and reconstruction

`simulate_qrda_counts()` measures the complete box.

`decode_qrda_counts()` decodes effective and redundant positions.

`reconstruct_qrda_signal()` returns only the first \(L\) effective samples.

## Arbitrary-length examples

| \(L\) | \(l\) | Box size | Padding |
|---:|---:|---:|---:|
| 1 | 1 | 2 | 1 |
| 3 | 2 | 4 | 1 |
| 5 | 3 | 8 | 3 |
| 15 | 4 | 16 | 1 |
| 16 | 4 | 16 | 0 |
| 17 | 5 | 32 | 15 |

## Reproducibility

```bash
python examples/audio/reproduce_qrda_primary_paper.py
python benchmarks/audio/run_qrda_protocol_comparison.py
```

Detailed documentation:

```text
docs/audio/qrda_primary_paper_validation.md
```

Machine-readable outputs:

```text
results/audio/qrda_primary_paper/
├── validation_report.json
├── statevector_support.csv
├── protocol_comparison.json
├── protocol_mapping.csv
└── circuit_metrics.csv
```

## Scope after v0.2.1

Completed: arbitrary-length QRDA, signed/unsigned translation, exact statevector validation, finite-shot reconstruction, resource/shot/noise benchmarks, primary-paper worked-example reproduction, and logical preparation-protocol validation.

Future work: QRDA connection and mixing, QRDA compression, real-QPU execution, error mitigation, and comparison against FRQA and later quantum-audio representations.
