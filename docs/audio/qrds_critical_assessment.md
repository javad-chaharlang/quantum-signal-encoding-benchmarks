# QRDS Critical Assessment

## 1. Scope

This assessment is restricted to QRDS properties directly reproduced or tested in the current repository. The validated baseline covers fixed-point conversion, state preparation, exact-state inspection, shot-based reconstruction, padding, local fractional modification, logical/transpiled resource measurement, and controlled FRQA comparison.

No claim is made here regarding quantum advantage, physical-hardware efficiency, watermarking security, steganographic undetectability, or robustness against attacks.

## 2. Numerical correctness

QRDS signed fixed-point conversion and inverse conversion are covered by automated tests. Values outside the configured range or off the selected fixed-point grid are rejected rather than silently rounded.

For `integer_bits=4` and `fractional_bits=3`, the validated paper-aligned boundaries are:

```text
+15.875 -> 01111111
-15.875 -> 10000001
```

The implementation deliberately follows the symmetric interval stated in the primary QRDS reference and excludes the conventional most-negative fixed-point two's-complement value. This should be treated as a paper-faithful convention and an interoperability consideration, not as a general property of two's-complement arithmetic.

## 3. State correctness and reconstruction

For

```text
[2.25, 0.75, -1.25, 1.50, 2.50, -1.00]
```

with two integer and two fractional bits, the representation uses:

```text
amplitude qubits: 5
position qubits:  3
total qubits:     8
box size:         8
padding:          2
resolution:       0.25
```

Exact-state support matches the expected QRDS representation, including zero amplitude in the two redundant addresses.

Shot-based reconstruction returns:

```text
[9/4, 3/4, -5/4, 3/2, 5/2, -1]
```

which is exactly the original fixed-point signal in the validated ideal-simulator experiment.

This does not guarantee exact recovery at arbitrary signal sizes, shot budgets, transpilation settings, or under physical noise.

## 4. Local fractional modification

A controlled modification changes only position 3 from `1.50` to `1.75`, exactly one amplitude quantum (`0.25`).

Exact-state comparison shows that only the amplitude basis state associated with that address is replaced. Shot reconstruction also differs only at position 3.

This validates representation-level locality. The current experiment rebuilds the encoded state from the modified classical signal; it is not a benchmark of a dedicated in-place quantum embedding operator.

## 5. Interpretation of total variation distance

The locality experiment exposes an important limitation of computational-basis TVD as a signal-distortion metric.

For a uniformly addressed eight-position state, replacing the amplitude basis word at one address moves probability mass `1/8` from one orthogonal basis state to another. Therefore the ideal basis-distribution TVD remains `1/8` whether the classical amplitude change is `0.25` or much larger, provided the amplitude word changes.

Thus a smaller classical amplitude change does not necessarily imply a smaller ideal basis-distribution change. Later information-hiding studies must report signal-domain distortion independently from quantum-state probability metrics.

## 6. Logical resources

For the validated six-sample QRDS example:

```text
qubits:          8
raw depth:       27
raw size:        40
X operations:    22
MCX operations:  15
Hadamard gates:   3
barriers:         2
```

Under the tested basis transpilation:

```text
transpiled depth: 322
transpiled size:  411
RZ:               212
CX:               164
SX:                23
X:                 12
barriers:           2
```

Logical-circuit figures are stored at:

```text
figures/audio/qrds/qrds_logical_circuit.png
figures/audio/qrds/qrds_logical_circuit.pdf
```

The increase after decomposition demonstrates that compact data-qubit count must not be conflated with inexpensive executable state preparation.

## 7. Controlled FRQA–QRDS comparison

With `fractional_bits=2`, scaling the QRDS samples by four produces:

```text
[9, 3, -5, 6, 10, -4]
```

A five-bit FRQA representation produces the same amplitude basis words. Dedicated regression tests confirm matching amplitude codes, register widths, total qubits, exact-state support after scaling, raw logical resources, and transpiled resources under the controlled settings.

The supported relation is:

```math
\mathrm{QRDS}(x,f) \equiv \mathrm{FRQA}(2^f x)
```

at the tested basis-preparation level.

This equivalence is conditional. It applies when the QRDS samples lie exactly on the fixed-point grid, the FRQA samples are scaled by `2^f`, the amplitude widths match, and both use the same address-controlled basis-writing strategy and transpilation settings.

## 8. Meaning of the comparison

The controlled result shows that QRDS does not introduce a fundamentally different basis-state preparation topology in this experiment.

Its important contribution is explicit fixed-point semantics.

For a fixed amplitude-register width:

```text
more fractional bits
-> finer resolution
-> smaller integer dynamic range
```

If integer dynamic range is instead held fixed, additional fractional bits require a wider amplitude register and therefore additional quantum resources.

Precision is not free.

## 9. Information-hiding implications

QRDS fractional bit planes are useful candidates for later embedding experiments because each bit plane has a known signal-domain significance.

That property is not a security guarantee. A later hiding method must independently define and evaluate embedding/extraction, capacity, classical distortion, quantum-state change, robustness, threat model, and detection or steganalysis performance.

## 10. Limitations

The current baseline is simulator-based.

It does not determine minimum shot budgets for larger signals.

Multi-controlled state preparation remains expensive after decomposition.

Padding creates redundant addresses for non-power-of-two signal lengths.

The range convention follows the symmetric interval stated in the primary paper rather than the full conventional two's-complement interval.

No dedicated in-place embedding primitive is implemented at this stage.

## 11. Software QA

At closure of the current QRDS implementation stage:

```text
repository tests:     137 passed
repository coverage:  85%
Ruff lint:            passed
git diff --check:     passed
```

Dedicated regression tests protect both QRDS correctness and the controlled FRQA–QRDS comparison.

## 12. Conclusion

The implemented QRDS baseline is sufficiently validated for use as a reproducible signed fixed-point quantum signal representation.

The strongest supported findings are:

1. fixed-point amplitudes round-trip correctly;
2. the validated compact signal produces the expected quantum-state support;
3. shot reconstruction succeeds in the tested ideal simulation;
4. a one-quantum fractional modification remains address-local;
5. basis-distribution TVD does not directly encode classical modification magnitude;
6. controlled QRDS preparation is equivalent to appropriately scaled FRQA preparation under the tested conditions;
7. QRDS's research relevance lies primarily in explicit fractional semantics;
8. fractional bit planes are useful candidates for later information-hiding experiments but do not constitute a security mechanism.

Under the project stop rule, no additional QRDS arithmetic implementation is required at this stage.
