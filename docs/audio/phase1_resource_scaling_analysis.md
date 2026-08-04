# Analysis of the Exploratory Resource-Scaling Run

## Verified execution

- Tests passed: `16`
- Project coverage: `91%`
- Benchmark module coverage: `86%`
- Environment:
  - Python `3.14.6`
  - Qiskit `2.5.1`
  - Qiskit Aer `0.17.2`
  - NumPy `2.5.1`
  - Matplotlib `3.11.1`

## Signal-length findings

With four amplitude qubits:

| Samples | Total qubits | Raw depth | Transpiled depth | Transpiled size | CX |
|---:|---:|---:|---:|---:|---:|
| 2 | 5 | 7 | 8 | 8 | 4 |
| 4 | 6 | 15 | 94 | 147 | 54 |
| 8 | 7 | 33 | 453 | 550 | 236 |
| 16 | 8 | 60 | 1807 | 2155 | 738 |
| 32 | 9 | 129 | 5918 | 6741 | 2286 |

From 2 to 32 samples, raw depth increased by about `18.4x`, while transpiled
depth increased by about `739.8x`. At 32 samples, transpiled depth was about
`45.9x` the raw depth. This confirms that decomposition overhead becomes dominant
as the time-register control width grows.

## Why the amplitude-resolution curve was non-monotonic

The random signals had the following total amplitude-bit Hamming weights:

```text
8, 18, 20, 19, 23, 20, 31
```

for amplitude widths from two to eight bits. The seven-bit case therefore contained
fewer set bits than the six-bit case, which reduced the number of controlled loading
operations. Across the seven points, the correlation between Hamming weight and
transpiled depth was approximately `0.95`.

The exploratory result is valid for those exact signals, but it cannot by itself
establish the isolated effect of amplitude-register width. The controlled benchmark
therefore adds sparse, repeated-random, and dense profiles.

## Timing limitation

The first transpilation took longer than several larger cases, indicating one-time
library initialization or warm-up overhead. The controlled benchmark performs an
explicit warm-up and reports the median of three timing repetitions.
