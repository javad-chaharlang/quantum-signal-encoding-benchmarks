# QRDA primary-paper validation and preparation-protocol comparison

## Scope

This document validates the repository implementation against the primary QRDA paper:

> Jian Wang, "QRDA: Quantum Representation of Digital Audio," *International Journal of Theoretical Physics*, vol. 55, pp. 1622-1641, 2016. DOI: 10.1007/s10773-015-2800-2.

The validation is intentionally separated into three levels:

1. **state-representation equivalence**;
2. **logical preparation-protocol equivalence**;
3. **physical gate decomposition after Qiskit transpilation**.

These levels must not be conflated.

## Primary-paper example

The paper begins from the 4-bit signed digital-audio sequence

```text
[0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0]
```

and translates it by the offset $2^{4-1}=8$, giving

```text
[8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8]
```

For this example:

- effective audio length: $L=15$;
- amplitude-register width: $q=4$;
- time-register width: $l=\lceil\log_2 15\rceil=4$;
- QRDA box size: $2^l=16$;
- redundant time positions: one;
- redundant state: $T=15$ with amplitude $0$;
- total data qubits: $q+l=8$.

The representation and redundant $2^l$-box construction are defined in Section 3.1 of the paper, especially Eqs. (5)-(7).

## State validated by the repository

The complete box state for the worked example is

```math
|B\rangle
=
\frac{1}{4}
\left(
\sum_{T=0}^{14}|D_T\rangle_{\mathrm{amp}}\otimes|T\rangle_{\mathrm{time}}
+
|0000\rangle_{\mathrm{amp}}\otimes|1111\rangle_{\mathrm{time}}
\right).
```

There are sixteen nonzero computational-basis components. Every component has probability

```math
\frac{1}{16}=0.0625.
```

The repository constructs the reference state independently from the preparation circuit and computes the fidelity between the reference and prepared states.

```math
F\left(|B_{\mathrm{paper}}\rangle,|B_{\mathrm{qiskit}}\rangle\right)=1
```

within numerical tolerance $10^{-12}$.

## Paper preparation protocol

Section 3.2 divides QRDA preparation into two steps.

### Step 1: blank QRDA box

The paper defines

```math
U_1=I^{\otimes q}\otimes H^{\otimes l}.
```

For the worked example this means four conceptual identity operations on the amplitude register and four Hadamard operations on the time register.

The repository emits the four Hadamard gates but omits explicit identity gates. This is logically equivalent because the amplitude register starts in $|0\rangle^{\otimes q}$ and the identity operation changes nothing.

### Step 2: conditional amplitude loading

For each effective time index $T$, the paper defines a setting operation $\Omega_T$. Each set amplitude bit $D_T^i=1$ is written by an $l$-controlled NOT operation.

For the 15-sample example,

```math
\sum_{T=0}^{14}\operatorname{popcount}(D_T)=33.
```

The paper independently confirms this value in Section 5.2.3 by stating that Fig. 4 contains 33 four-controlled NOT operations before DPCM compression.

The repository therefore expects exactly 33 logical `mcx` amplitude-write operations.

## Open and closed controls

Figure 4 uses open and closed control symbols on the time register. A closed control activates on $|1\rangle$ and an open control activates on $|0\rangle$.

The repository uses Qiskit's all-one `mcx` control convention. Zero-valued controls are implemented by applying `X` before and after the `mcx`.

Across effective time positions $0,\ldots,14$, there are 32 zero control bits. Therefore the present implementation contains

```math
2\times32=64
```

`X` wrapper operations.

These wrappers are an implementation detail and are not additional QRDA amplitude writes.

## Equivalence claims

### State level

**Exact.** The independently constructed paper state and the Qiskit-prepared state must have fidelity one.

### Logical preparation level

**Equivalent.**

| Quantity | Paper | Repository |
|---|---:|---:|
| Hadamard operations | 4 | 4 |
| Controlled amplitude writes | 33 | 33 |
| Padding state | $T=15,\ D_T=0$ | $T=15,\ D_T=0$ |
| State fidelity | 1 | 1 |

### Gate-for-gate physical level

**Not identical and not claimed to be identical.**

The paper uses symbolic $l$-controlled NOT gates and diagrammatic open/closed controls. Qiskit realizes the same logical conditions through `mcx` plus `X` conjugation for zero-controls. The transpiler then decomposes `mcx` into the selected basis gates.

Therefore the paper's count of 33 symbolic four-controlled NOT operations must not be compared numerically with the final transpiled CX count as if they were the same resource.

## Transpilation protocol

The reproducibility benchmark uses:

```text
basis gates: rz, sx, x, cx
seed_transpiler: 42
optimization levels: 0 and 1
```

It records:

- qubit count;
- circuit depth;
- circuit size;
- operation counts;
- final CX count.

These transpiled metrics characterize this repository and software configuration, not the abstract resource count in the 2016 paper.

## Reproduction commands

Primary worked-example validation:

```bash
python examples/audio/reproduce_qrda_primary_paper.py
```

Preparation-protocol comparison:

```bash
python benchmarks/audio/run_qrda_protocol_comparison.py
```

The protocol benchmark creates:

```text
results/audio/qrda_primary_paper/
├── protocol_comparison.json
├── protocol_mapping.csv
└── circuit_metrics.csv
```

in addition to the statevector and reconstruction outputs generated by the primary-paper reproduction script.

## Validation criteria

| Criterion | Expected |
|---|---:|
| Effective samples | 15 |
| Amplitude qubits | 4 |
| Time qubits | 4 |
| Total qubits | 8 |
| QRDA box size | 16 |
| Padding states | 1 |
| Nonzero state support | 16 |
| State fidelity | 1.0 |
| Hadamard gates | 4 |
| Logical controlled writes | 33 |
| Qiskit `mcx` writes | 33 |
| Zero-control `X` wrappers | 64 |

## Scientific conclusion

The repository implementation reproduces the primary paper's QRDA state and its logical amplitude-loading protocol for the published 15-sample example.

This supports the statement that the implementation is **state-equivalent and logically preparation-equivalent** to the worked QRDA example.

It does not support a claim that the Qiskit circuit is physically gate-for-gate identical to the paper diagram, because zero-controls and multi-controlled gates are represented and decomposed differently by the software stack.

Real-QPU execution remains a separate future validation layer.
