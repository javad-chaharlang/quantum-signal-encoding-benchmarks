# Basis-Encoded Quantum Audio Representation

## Status

Implemented in v0.1.0 as a transparent baseline. This method is **not QRDA, FRQA, or QPAM**.

## Classical input

Let a quantized digital audio signal contain $N=2^n$ unsigned integer samples:

```math
\mathbf{a}
=
[a_0,a_1,\ldots,a_{N-1}],
\qquad
0 \leq a_t < 2^m.
```

The representation uses:

- $n=\log_2 N$ time qubits
- $m$ amplitude qubits
- $n+m$ data qubits in total

## Quantum state

The prepared state is

```math
|A\rangle
=
\frac{1}{\sqrt{N}}
\sum_{t=0}^{N-1}
|a_t\rangle_{\mathrm{amp}}
|t\rangle_{\mathrm{time}}.
```

The time register is first placed in a uniform superposition. Multi-controlled bit flips then write the binary amplitude associated with each time basis state into the amplitude register.

## Register convention

Within each register, qubit $i$ stores binary bit $i$, following a little-endian indexing convention. In the full circuit, amplitude qubits precede time qubits.

Therefore, the computational-basis integer corresponding to $(t,a_t)$ is

```math
\mathrm{index}
=
a_t+t\,2^m.
```

The equivalent bit-shift expression in Python is:

```python
basis_index = amplitude + (time_index << amplitude_bits)
```

This convention is tested explicitly through exact statevector probabilities.

## Preparation procedure

1. Validate that the signal length is a non-zero power of two.
2. Validate unsigned integer quantization.
3. Allocate amplitude and time registers.
4. Apply Hadamard gates to every time qubit.
5. For each sample index $t$, convert zero-valued control bits into positive controls with temporary $X$ gates.
6. Apply controlled or multi-controlled $X$ gates to write each non-zero amplitude bit.
7. Restore temporary control inversions.

## Reconstruction

The circuit is measured in the computational basis. Each outcome is separated into amplitude and time fields. The modal amplitude observed for each time index is used as the reconstructed value.

For an ideal basis encoding, every observed outcome associated with a given time index has exactly one amplitude. Finite shots mainly determine whether every time index is observed at least once.

## Current limitations

- Only unsigned integer amplitudes are supported.
- The signal length must be a power of two.
- Generic multi-controlled gates can lead to substantial depth after decomposition.
- State preparation scales with signal length and amplitude bit width.
- This representation does not by itself demonstrate quantum advantage.
- Modal reconstruction is suitable for the deterministic basis representation, not probability-amplitude encodings.

## Planned experiments

- Shot count versus complete-index coverage
- Raw versus transpiled circuit resources
- Scaling with sample count and amplitude resolution
- Depolarizing and readout-noise sensitivity
- Comparison with QRDA, FRQA, and QPAM/SQPAM
