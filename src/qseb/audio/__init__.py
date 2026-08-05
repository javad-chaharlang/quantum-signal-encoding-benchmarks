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
from qseb.audio.qrda_encoding import (
    QRDAEncodingSpec,
    build_qrda_circuit,
    decode_qrda_counts,
    exact_qrda_probabilities,
    qrda_resource_metrics,
    reconstruct_qrda_signal,
    simulate_qrda_counts,
)

__all__ = [
    "AudioEncodingSpec",
    "QRDAEncodingSpec",
    "build_basis_encoded_audio_circuit",
    "build_qrda_circuit",
    "circuit_resource_metrics",
    "decode_measurement_counts",
    "decode_qrda_counts",
    "exact_basis_probabilities",
    "exact_qrda_probabilities",
    "qrda_resource_metrics",
    "reconstruct_from_counts",
    "reconstruct_qrda_signal",
    "simulate_counts",
    "simulate_qrda_counts",
]
