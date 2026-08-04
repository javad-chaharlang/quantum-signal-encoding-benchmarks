# Calibration-Derived Hardware-Noise Analysis

## Execution validation

- Backend snapshot: **FakeNairobiV2**
- Hardware execution: **False**
- Live calibration: **False**
- Raw runs: **120**
- Global aggregated conditions: **8**
- Layout-level aggregated conditions: **40**
- Calibration records: **54**
- Qubit calibration records: **7**
- Instruction calibration records: **47**
- Missing values in benchmark result tables: **0**
- Duplicate raw run identifiers: **0**

The benchmark grid is complete: two signal lengths, four noise conditions, five
transpiler seeds, and three simulator seeds produced exactly 120 raw runs.

## Snapshot calibration profile

| Calibration quantity | Value |
|:---|---:|
| Mean readout error | 0.0266 |
| Maximum readout error | 0.0580 |
| Mean CX error | 0.0088 |
| Maximum CX error | 0.0126 |
| Mean T1 | 96.2 µs |
| Mean T2 | 84.2 µs |

The snapshot is heterogeneous: readout and two-qubit errors vary across physical
qubits and directed edges. This motivates the explicit layout analysis.

## Hardware-mapped circuit exposure

| Samples | Logical qubits | Mean depth | Mean two-qubit gates | Mean success proxy |
|---:|---:|---:|---:|---:|
| 4 | 6 | 188.0 | 92.8 | 0.4365 |
| 8 | 7 | 751.8 | 432.6 | 0.0228 |

Moving from four to eight samples increased hardware-mapped depth by
**4.00x**
and the two-qubit gate count by
**4.66x**.
No explicit SWAP operations remained in the transpiled circuits, but the longer
circuit still accumulated a much larger calibrated error budget.

The independent-gate success proxy is a diagnostic product of per-instruction
success factors. It is not a circuit-fidelity estimate.

## Global noise-ablation results

| Samples | Condition | Exact rate | Modal accuracy | Correct-state fraction | Amplitude BER | Joint TVD |
|---:|:---|---:|---:|---:|---:|---:|
| 4 | ideal | 1.000 | 1.000 | 1.000 | 0.0000 | 0.014 |
| 4 | readout_only | 1.000 | 1.000 | 0.861 | 0.0470 | 0.139 |
| 4 | gate_thermal | 1.000 | 1.000 | 0.451 | 0.2255 | 0.549 |
| 4 | full_calibration | 1.000 | 1.000 | 0.397 | 0.2504 | 0.603 |
| 8 | ideal | 1.000 | 1.000 | 1.000 | 0.0000 | 0.027 |
| 8 | readout_only | 1.000 | 1.000 | 0.855 | 0.0461 | 0.145 |
| 8 | gate_thermal | 0.000 | 0.192 | 0.087 | 0.4642 | 0.913 |
| 8 | full_calibration | 0.000 | 0.158 | 0.085 | 0.4697 | 0.915 |

## Principal findings

### 1. Gate and thermal errors dominate the device-derived model

For four samples, readout-only noise retained a correct-state fraction of
**0.861**, while gate-plus-thermal
noise reduced it to **0.451**.

For eight samples, the corresponding values were
**0.855** and
**0.087**. The longer circuit therefore
became almost completely distributionally corrupted under the gate-plus-thermal
component alone.

Adding readout noise to gate-plus-thermal noise reduced the correct-state fraction
by only **0.054**
for four samples and
**0.002**
for eight samples. In the longer circuit, gate and thermal errors already dominate
the failure.

### 2. The seven-qubit signal fails modal reconstruction

For the eight-sample, seven-logical-qubit circuit:

- ideal exact reconstruction rate: **1.000**
- readout-only exact reconstruction rate: **1.000**
- gate-plus-thermal exact reconstruction rate: **0.000**
- full-calibration exact reconstruction rate: **0.000**

Under the full calibration-derived model, mean modal amplitude accuracy was only
**0.158**, the correct-state fraction was
**0.085**, and joint TVD reached
**0.915**.

### 3. Exact reconstruction still hides severe corruption for four samples

The four-sample circuit retained exact and modal reconstruction rates of one under
the full model. Nevertheless:

- correct-state fraction: **0.397**
- amplitude bit-error rate: **0.250**
- joint TVD: **0.603**

The modal decoder remains correct because the intended amplitude is still the most
frequent outcome at every time index. Distribution-level metrics remain essential.

### 4. Layout optimization has measurable but limited impact

For four samples, the best full-calibration layout used seed
**52** and achieved a correct-state fraction of
**0.407**. The worst used seed
**62** and achieved
**0.383**, an absolute range of
**0.024**.

For eight samples, the layout range was only
**0.0016**. All seven physical qubits are required, so
the transpiler has much less freedom; only
**1** unique initial layout was selected
across the five seeds.

The correlation between the diagnostic success proxy and observed correct-state
fraction was **0.896** for four samples and
**0.837** for eight samples. These
correlations are descriptive only because each group contains five layouts and some
layouts repeat.

### 5. Full index coverage does not imply fidelity

Every run observed all time indices, but time-marginal TVD ranged from
**0.0024** to
**0.1152**. The main failure mode remains
amplitude and joint-state corruption, not missing time indices.

## Comparison with the synthetic-noise phase

The earlier synthetic study established monotonic stress-test behavior. This
snapshot-derived study adds three practical features:

1. heterogeneous qubit and edge errors;
2. thermal relaxation derived from calibrated durations and T1/T2;
3. hardware-aware physical layouts and target constraints.

Both studies reach the same central conclusion: deeper, two-qubit-heavy explicit
state preparation is the main robustness bottleneck.

## Interpretation boundary

`FakeNairobiV2` is a historical calibration snapshot used in simulation. These are
not live calibration results and not measurements from a real QPU. Automatic Aer
device models remain approximate and do not capture all crosstalk, leakage,
correlated errors, pulse effects, or temporal drift.
