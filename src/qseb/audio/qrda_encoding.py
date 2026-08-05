"""Quantum Representation of Digital Audio (QRDA).

This module exposes the repository's validated unsigned digital-audio encoder
under QRDA-specific scientific names. The prepared state is

    |S> = 1/sqrt(N) sum_t |S_t>_amplitude |t>_time,

where the quantized amplitude ``S_t`` and time index ``t`` are stored in two
entangled computational-basis registers.

The implementation supports unsigned integer amplitudes. Bipolar audio samples
must be translated to a non-negative quantization range before encoding. The
legacy ``basis_encoding`` API remains available for backward compatibility.

Primary reference:
    Wang, J. (2016). QRDA: Quantum Representation of Digital Audio.
    International Journal of Theoretical Physics, 55, 1622-1641.
    https://doi.org/10.1007/s10773-015-2800-2
"""

from __future__ import annotations

from qseb.audio.basis_encoding import (
    AudioEncodingSpec,
    build_basis_encoded_audio_circuit,
    circuit_resource_metrics,
    decode_measurement_counts,
    exact_basis_probabilities,
    reconstruct_from_counts,
    simulate_counts,
)

QRDAEncodingSpec = AudioEncodingSpec
build_qrda_circuit = build_basis_encoded_audio_circuit
exact_qrda_probabilities = exact_basis_probabilities
simulate_qrda_counts = simulate_counts
decode_qrda_counts = decode_measurement_counts
reconstruct_qrda_signal = reconstruct_from_counts
qrda_resource_metrics = circuit_resource_metrics

__all__ = [
    "QRDAEncodingSpec",
    "build_qrda_circuit",
    "decode_qrda_counts",
    "exact_qrda_probabilities",
    "qrda_resource_metrics",
    "reconstruct_qrda_signal",
    "simulate_qrda_counts",
]
