"""Tests for the QRDA scientific API and legacy compatibility."""

from __future__ import annotations

import math

import pytest

from qseb.audio import (
    QRDAEncodingSpec,
    build_basis_encoded_audio_circuit,
    build_qrda_circuit,
    decode_qrda_counts,
    exact_basis_probabilities,
    exact_qrda_probabilities,
    reconstruct_qrda_signal,
    simulate_qrda_counts,
)


def test_qrda_spec_exposes_box_metadata() -> None:
    _, spec = build_qrda_circuit([3, 6, 2, 5], amplitude_bits=3)

    assert isinstance(spec, QRDAEncodingSpec)
    assert spec.num_samples == 4
    assert spec.amplitude_bits == 3
    assert spec.time_bits == 2
    assert spec.box_size == 4
    assert spec.padding_count == 0
    assert math.isclose(spec.padding_fraction, 0.0)


def test_qrda_and_legacy_builders_match_for_power_of_two_length() -> None:
    samples = [3, 6, 2, 5]
    qrda_circuit, qrda_spec = build_qrda_circuit(samples, amplitude_bits=3)
    legacy_circuit, legacy_spec = build_basis_encoded_audio_circuit(
        samples,
        amplitude_bits=3,
    )

    assert qrda_spec.num_samples == legacy_spec.num_samples
    assert qrda_spec.amplitude_bits == legacy_spec.amplitude_bits
    assert qrda_spec.time_bits == legacy_spec.time_bits
    assert exact_qrda_probabilities(qrda_circuit, qrda_spec) == (
        exact_basis_probabilities(legacy_circuit, legacy_spec)
    )


def test_qrda_exact_state_matches_unsigned_samples() -> None:
    samples = [3, 6, 2, 5]
    circuit, spec = build_qrda_circuit(samples, amplitude_bits=3)
    probabilities = exact_qrda_probabilities(circuit, spec)

    assert set(probabilities) == {
        (time_index, amplitude) for time_index, amplitude in enumerate(samples)
    }
    for probability in probabilities.values():
        assert math.isclose(probability, 0.25, abs_tol=1e-12)


def test_qrda_shot_reconstruction() -> None:
    samples = [3, 6, 2, 5]
    circuit, spec = build_qrda_circuit(samples, amplitude_bits=3)
    counts = simulate_qrda_counts(circuit, shots=2048, seed_simulator=42)

    assert reconstruct_qrda_signal(counts, spec) == samples


def test_qrda_known_count_decoding() -> None:
    _, spec = build_qrda_circuit([3, 6, 2, 5], amplitude_bits=3)
    counts = {
        "00011": 10,
        "01110": 11,
        "10010": 12,
        "11101": 13,
    }

    decoded = decode_qrda_counts(counts, spec)

    assert decoded[0][3] == 10
    assert decoded[1][6] == 11
    assert decoded[2][2] == 12
    assert decoded[3][5] == 13


def test_qrda_rejects_negative_amplitudes() -> None:
    with pytest.raises(ValueError, match="unsigned"):
        build_qrda_circuit([-1, 0], amplitude_bits=2)
