# QRDA method and implementation scope

## Representation

The repository implements the unsigned Quantum Representation of Digital Audio
(QRDA) state

\[
|S\rangle =
\frac{1}{\sqrt{N}}
\sum_{t=0}^{N-1}
|S_t\rangle_{\mathrm{amplitude}}
|t\rangle_{\mathrm{time}},
\]

where \(N=2^k\), the time register contains \(k\) qubits, and the amplitude
register stores one quantized integer \(S_t\) for each sample index.

## Signed audio samples

The current encoder accepts amplitudes in

\[
0 \leq S_t \leq 2^m-1.
\]

A bipolar waveform must first be translated into an unsigned range, for example

\[
S_t = x_t + 2^{m-1}.
\]

The offset must be recorded and removed after reconstruction. Direct signed
amplitudes will be studied in the FRQA phase.

## Scope of v0.2

The previous `basis_encoding` implementation already prepared the QRDA state
structure. Version 0.2 adds QRDA-specific names, preserves the legacy API,
documents the unsigned constraint, and tests equivalence between both APIs.

This formalization establishes equivalence at the state-representation level.
Reproduction of the primary paper's exact worked example and gate-level
preparation protocol remains a separate validation item.

## Primary reference

Wang, J. (2016). QRDA: Quantum Representation of Digital Audio.
*International Journal of Theoretical Physics, 55*, 1622-1641.
https://doi.org/10.1007/s10773-015-2800-2
