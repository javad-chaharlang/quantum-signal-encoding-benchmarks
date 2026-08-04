"""Quantum audio encoding methods."""

from qseb.audio.basis_encoding import (
    AudioEncodingSpec,
    build_basis_encoded_audio_circuit,
    circuit_resource_metrics,
    decode_measurement_counts,
    exact_basis_probabilities,
    reconstruct_from_counts,
    simulate_counts,
)

__all__ = [
    "AudioEncodingSpec",
    "build_basis_encoded_audio_circuit",
    "circuit_resource_metrics",
    "decode_measurement_counts",
    "exact_basis_probabilities",
    "reconstruct_from_counts",
    "simulate_counts",
]
