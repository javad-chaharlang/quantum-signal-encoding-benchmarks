# FRQA — Minimal Validated Audio Baseline

## Scope

FRQA is included in this repository as a **minimal comparison baseline** for QRDA, not as a new standalone subproject.

The purpose is to answer one focused question:

> Does direct two's-complement signed-amplitude representation provide a more natural foundation for quantum audio modification and information hiding than QRDA's unsigned core plus offset preprocessing?

The repository therefore implements only the representation, preparation, exact-state validation, measurement/reconstruction path, one primary-paper example, and the comparison properties needed for later information-hiding work.

Signal addition, inversion, delay, reversal, and other FRQA-specific operations are deferred unless a downstream experiment requires them.

## Primary reference

Yan, F., Iliyasu, A. M., Guo, Y., & Yang, H. (2018). Flexible representation and manipulation of audio signals on quantum computers. *Theoretical Computer Science, 752*, 71–85. https://doi.org/10.1016/j.tcs.2017.12.025

## Signed digital-audio model

The paper models a digital audio signal as

```math
A=[a_0,a_1,\ldots,a_{L-1}],
```

with each q-bit sample in the signed range

```math
-2^{q-1} \le a_t \le 2^{q-1}-1.
```

Unlike the unsigned QRDA core, FRQA represents bipolar amplitudes directly with q-bit **two's-complement notation**.

## FRQA state

For a 2^l-sample signal, the FRQA state is

```math
|A\rangle=
\frac{1}{2^{l/2}}
\sum_{t=0}^{2^l-1}
|S_t\rangle_{\mathrm{amp}}\otimes|t\rangle_{\mathrm{time}},
```

where `|S_t>` is the q-qubit two's-complement representation of the signed amplitude and `|t>` is the l-qubit time index.

The representation therefore uses `q + l` data qubits.

For an arbitrary positive signal length L, the paper uses

```math
l=
\begin{cases}
\lceil\log_2L\rceil, & L>1,\\
1, & L=1,
\end{cases}
```

and assigns zero amplitude to the `2^l-L` redundant time positions.

## Two's-complement convention

For q amplitude qubits, the valid signed range is

```math
[-2^{q-1},\;2^{q-1}-1].
```

The repository API accepts signed integer samples directly and converts them to q-bit two's-complement codes using

```text
value >= 0  -> code = value
value < 0   -> code = 2^q + value
```

For q=3 this produces:

| Signed amplitude | Two's-complement code |
|---:|:---:|
| -4 | 100 |
| -3 | 101 |
| -2 | 110 |
| -1 | 111 |
| 0 | 000 |
| 1 | 001 |
| 2 | 010 |
| 3 | 011 |

This is the signed representation used by FRQA. The primary paper also explains preparation from unsigned ADC-resolution values via a quantization/conversion step; the repository's signed-input API starts after that classical interpretation and writes the resulting two's-complement sample values directly.

## Preparation strategy

The implementation follows the two conceptual stages in the primary paper:

1. Apply Hadamard gates to the time register to prepare the uniform superposition over all `2^l` time positions.
2. For each effective time index, conditionally write the corresponding q-bit two's-complement amplitude into the amplitude register.

Open controls are represented in Qiskit by temporary `X` conjugation of time qubits whose desired control value is zero.

The repository does **not** claim gate-for-gate identity with the paper's symbolic circuit decompositions.

## Primary-paper Fig. 1 example

The minimal validated example is the 13-sample waveform shown in Fig. 1 of the paper:

```text
[0, 1, 0, -1, 0, 2, 3, 1, -1, -2, -1, 0, 0]
```

The paper uses:

- amplitude width `q = 3`;
- effective signal length `L = 13`;
- time width `l = 4`;
- total data qubits `q + l = 7`;
- FRQA box size `2^l = 16`;
- three redundant time positions with zero amplitude.

The repository validates all 16 state-support positions with probability `1/16` and reconstructs the 13 effective signed samples.

Run:

```bash
python examples/audio/reproduce_frqa_baseline.py
```

## QRDA versus FRQA — research relevance

| Property | QRDA | FRQA |
|---|---|---|
| Core amplitude type | Unsigned basis value | Signed two's-complement basis value |
| Signed classical audio | Offset preprocessing | Direct signed representation |
| Time addressing | Explicit time register | Explicit time register |
| Local sample modification | Possible with controlled writes | Possible with controlled writes |
| Arithmetic around zero | Requires unsigned interpretation/translation | Natural bipolar arithmetic model |
| Arbitrary non-power-of-two L | Zero-amplitude redundant states | Zero-amplitude redundant states |
| Information-hiding relevance | Discrete sample-addressed baseline | Signed sample-addressed baseline |

### Current interpretation

FRQA removes QRDA's unsigned-core limitation and therefore provides a cleaner representation for studying modifications whose meaning depends on the sign and midrange of the waveform.

This does **not** establish implementation efficiency or quantum advantage. Controlled sample addressing still introduces non-trivial circuit overhead, and later information-hiding experiments must report the incremental cost of embedding operations.

## Stop rule

Once this baseline has passed exact-state and reconstruction validation and the QRDA/FRQA comparison is documented, no additional FRQA operation is required before moving to the image foundations and then to quantum information hiding.
