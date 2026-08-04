# Noise-Sensitivity Analysis: Basis-Encoded Quantum Audio

## Execution validation

- Raw noisy runs: **130**
- Aggregated conditions: **26**
- Signal lengths: `[4, 8]`
- Simulator seeds: `[42, 52, 62, 72, 82]`
- Shots per run: `1024`
- Noise families: `gate`, `readout`, `combined`
- Severity levels: `low`, `moderate`, `high`, `severe`
- Missing numerical values: **0**
- Duplicate raw conditions: **0**
- Hardware execution: **False**
- Backend-calibration-derived noise: **False**

## Circuit-size context

| Samples | Total qubits | Transpiled depth | Transpiled CX count |
|---:|---:|---:|---:|
| 4 | 6 | 95 | 54 |
| 8 | 7 | 454 | 236 |

Doubling the signal length from four to eight samples increased transpiled depth by
approximately **4.78x**
and CX count by **4.37x**.
This resource increase explains why the longer signal is substantially more
sensitive to accumulated gate errors.

## Principal results

### 1. Gate noise dominates readout noise

At the **moderate** setting:

| Samples | Family | Correct-state fraction | Amplitude BER | Joint TVD |
|---:|:---|---:|---:|---:|
| 4 | gate | 0.711 | 0.1257 | 0.289 |
| 4 | readout | 0.944 | 0.0197 | 0.062 |
| 4 | combined | 0.674 | 0.1398 | 0.326 |
| 8 | gate | 0.251 | 0.3583 | 0.749 |
| 8 | readout | 0.941 | 0.0182 | 0.078 |
| 8 | combined | 0.242 | 0.3639 | 0.758 |

For eight samples, moderate gate noise reduced the correct-state fraction to
**0.251**, whereas
moderate readout noise retained **0.941**.
The combined condition closely followed the gate-only condition, showing that
accumulated gate errors are the dominant limitation in this circuit.

### 2. Longer signals show a sharp modal-reconstruction collapse

For the eight-sample circuit:

| Severity | Gate modal accuracy | Combined modal accuracy | Gate exact rate | Combined exact rate |
|:---|---:|---:|---:|---:|
| low | 1.000 | 1.000 | 1.000 | 1.000 |
| moderate | 1.000 | 1.000 | 1.000 | 1.000 |
| high | 0.300 | 0.275 | 0.000 | 0.000 |
| severe | 0.050 | 0.025 | 0.000 | 0.000 |

Modal reconstruction remained perfect through the moderate level but collapsed at
the high level. Under severe gate noise, mean modal amplitude accuracy fell to
**0.050**.

### 3. Exact reconstruction alone can hide severe distribution corruption

For four samples, exact reconstruction and modal accuracy remained equal to one at
every tested severity. However, under severe gate noise:

- correct ideal-basis shot fraction: **0.222**
- amplitude bit-error rate: **0.367**
- joint-distribution TVD: **0.778**

The modal decoder still selected the correct amplitude because the correct outcome
remained the most frequent outcome for every time index. Therefore, binary exact
reconstruction must not be used as the sole robustness metric.

### 4. Readout noise is comparatively well tolerated by the modal decoder

Even at the severe readout setting, modal accuracy and exact reconstruction remained
one for both signal lengths. Nevertheless, the correct-state fraction fell to
**0.733** for four
samples and **0.722**
for eight samples. This again shows why distributional and bit-error metrics are
necessary beside modal reconstruction.

### 5. Time-index coverage is not the limiting factor here

Every run achieved full time-index coverage. Time-marginal TVD remained between
**0.0117** and
**0.0645**, while amplitude-related metrics
degraded strongly. The principal failure mode in this experiment is therefore
amplitude corruption rather than missing time indices.

## Metric monotonicity

For each signal length and each non-ideal noise family:

- correct-state fraction decreased monotonically with severity;
- amplitude bit-error rate increased monotonically;
- joint-distribution TVD increased monotonically.

This supports the internal consistency of the synthetic stress-test grid.

## Statistical caution

Each aggregated condition contains five simulator seeds. Consequently, exact
reconstruction rates have a coarse resolution of `0.2`, and Wilson intervals are
wide. Continuous metrics such as modal accuracy, correct-state fraction, amplitude
BER, and joint TVD should be treated as the primary evidence.

## Main conclusion

The present explicit basis-encoding circuit is much more vulnerable to accumulated
gate noise than to symmetric readout noise. This vulnerability rises sharply with
circuit depth and CX count. The experiment also demonstrates that modal exact
reconstruction can remain perfect even when most measured basis states are wrong,
so robust evaluation requires both reconstruction and distribution-level metrics.

## Interpretation boundary

These results use independent synthetic depolarizing and symmetric readout channels.
They do not represent a specific physical backend, coupling map, thermal-relaxation
model, crosstalk process, leakage mechanism, calibration drift, or error-mitigation
pipeline.
