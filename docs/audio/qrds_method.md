# QRDS — Minimal Validated Fixed-Point Audio Baseline

## Scope

QRDS is included as a minimal signed fixed-point quantum signal representation baseline. The implementation is intentionally limited to the evidence needed for later representation-suitability and information-hiding research.

The focused question is:

> What does explicit signed fixed-point amplitude semantics add beyond an integer two's-complement representation such as FRQA?

The baseline covers fixed-point conversion, state preparation, exact-state validation, shot-based reconstruction, local fractional modification, resource measurement, and a controlled FRQA comparison. General QRDS arithmetic operations are deferred unless a downstream experiment requires them.

## Primary reference

Li, P., Wang, B., Xiao, H., & Liu, X. (2018). Quantum Representation and Basic Operations of Digital Signals. *International Journal of Theoretical Physics, 57*, 3242–3270. DOI: 10.1007/s10773-018-3841-0

## Fixed-point amplitude model

The repository API uses:

- `integer_bits = m`
- `fractional_bits = f`
- `amplitude_bits = 1 + m + f`

The amplitude quantum is

```math
\Delta = 2^{-f}.
```

Following the symmetric interval stated in the primary reference, the implementation accepts

```math
-2^m + 2^{-f} \le x_t \le 2^m - 2^{-f}.
```

The conventional most-negative two's-complement value `-2^m` is deliberately excluded. This is a paper-faithful QRDS convention, not a general limitation of fixed-point arithmetic.

For `integer_bits=4` and `fractional_bits=3`, the validated boundaries are:

```text
+15.875 -> 01111111
-15.875 -> 10000001
```

## QRDS state

For `L` effective samples and `k` position qubits, the implemented state is

```math
|X\rangle =
\frac{1}{\sqrt{2^k}}
\sum_{t=0}^{2^k-1}
|x_t\rangle_{\mathrm{amp}}
|t\rangle_{\mathrm{pos}}.
```

The position width is `ceil(log2(L))` for `L>1` and one qubit for a singleton signal. Unused addresses are represented with zero amplitude.

The total number of data qubits is

```math
1+m+f+k.
```

## Validated compact example

The validated signal is:

```text
[2.25, 0.75, -1.25, 1.50, 2.50, -1.00]
```

with:

```text
integer_bits:      2
fractional_bits:   2
amplitude qubits:  5
position qubits:   3
total qubits:      8
box size:          8
padding positions: 2
amplitude quantum: 0.25
```

The fixed-point words are:

| Amplitude | QRDS word |
|---:|:---:|
| 2.25 | 01001 |
| 0.75 | 00011 |
| -1.25 | 11011 |
| 1.50 | 00110 |
| 2.50 | 01010 |
| -1.00 | 11100 |

Exact-state validation confirms the expected support with probability `1/8` per address. Shot-based reconstruction returns the original six effective samples exactly in the validated ideal-simulator experiment.

Run:

```bash
python examples/audio/reproduce_qrds_baseline.py
```

## Local fractional modification

The locality experiment changes only position 3:

```text
1.50 -> 1.75
```

With two fractional bits this is exactly one amplitude quantum, `0.25`. Exact-state comparison shows that only the basis branch associated with position 3 changes, and shot reconstruction also changes only that effective sample.

The ideal computational-basis total variation distance is `1/8`. This validates representation-level addressability; it does not establish watermarking or steganographic security.

## Controlled FRQA comparison

With `f=2`, multiplying the QRDS signal by `2^f=4` gives:

```text
[9, 3, -5, 6, 10, -4]
```

A five-bit FRQA representation produces the same amplitude words:

```text
QRDS: 01001 00011 11011 00110 01010 11100
FRQA: 01001 00011 11011 00110 01010 11100
```

Dedicated regression tests validate identical codes, register widths, total qubits, exact-state support after scaling, raw logical resources, and transpiled resources under the tested settings.

Under these controlled conditions,

```math
\mathrm{QRDS}(x,f) \equiv \mathrm{FRQA}(2^f x)
```

at the basis-state preparation level.

This is not a claim of universal equivalence between the complete QRDS and FRQA frameworks. The meaningful distinction is numerical semantics: QRDS assigns an explicit binary point and fractional resolution to the amplitude word, while FRQA interprets the corresponding word as a signed integer.

## Information-hiding relevance

Fractional QRDS bit planes provide a precisely defined signal-domain modification scale. This makes them useful candidates for later embedding experiments.

However, a smaller classical amplitude change does not automatically imply a smaller change in the ideal computational-basis probability distribution. Future information-hiding experiments should therefore report quantum-state metrics and classical signal-domain distortion separately.

## Stop rule

The QRDS baseline is complete once fixed-point correctness, exact-state preparation, reconstruction, locality, resource characterization, and the controlled FRQA comparison are validated.

Additional QRDS arithmetic operations are deferred until a downstream experiment requires them.
