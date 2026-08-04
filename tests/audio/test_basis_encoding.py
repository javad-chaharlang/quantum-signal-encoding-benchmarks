"""Tests for basis-encoded quantum audio."""

from __future__ import annotations

import math

import pytest

from qseb.audio import (
    build_basis_encoded_audio_circuit,
    decode_measurement_counts,
    exact_basis_probabilities,
    reconstruct_from_counts,
    simulate_counts,
)


def test_builds_expected_register_size() -> None:
    circuit, spec = build_basis_encoded_audio_circuit([3, 6, 2, 5], amplitude_bits=3)
    assert spec.num_samples == 4
    assert spec.time_bits == 2
    assert spec.amplitude_bits == 3
    assert spec.total_qubits == 5
    assert circuit.num_qubits == 5
    assert circuit.num_clbits == 0


def test_single_sample_uses_only_amplitude_register() -> None:
    circuit, spec = build_basis_encoded_audio_circuit([5], amplitude_bits=3)
    assert spec.time_bits == 0
    assert circuit.num_qubits == 3
    assert exact_basis_probabilities(circuit, spec) == {(0, 5): 1.0}


def test_exact_state_matches_input_signal() -> None:
    samples = [3, 6, 2, 5]
    circuit, spec = build_basis_encoded_audio_circuit(samples, amplitude_bits=3)
    probabilities = exact_basis_probabilities(circuit, spec)

    assert set(probabilities) == {(index, value) for index, value in enumerate(samples)}
    for probability in probabilities.values():
        assert math.isclose(probability, 0.25, abs_tol=1e-12)


def test_shot_based_reconstruction() -> None:
    samples = [3, 6, 2, 5]
    circuit, spec = build_basis_encoded_audio_circuit(samples, amplitude_bits=3)
    counts = simulate_counts(circuit, shots=2048, seed_simulator=42)
    assert reconstruct_from_counts(counts, spec) == samples


def test_decode_known_bitstrings() -> None:
    _, spec = build_basis_encoded_audio_circuit([3, 6, 2, 5], amplitude_bits=3)
    # Qubit-order states: amplitude bits first, then time bits.
    # Qiskit count strings are rendered in reverse classical-bit order.
    counts = {
        "00011": 10,  # t=0, amplitude=3
        "01110": 11,  # t=1, amplitude=6
        "10010": 12,  # t=2, amplitude=2
        "11101": 13,  # t=3, amplitude=5
    }
    decoded = decode_measurement_counts(counts, spec)
    assert decoded[0][3] == 10
    assert decoded[1][6] == 11
    assert decoded[2][2] == 12
    assert decoded[3][5] == 13


@pytest.mark.parametrize(
    ("samples", "message"),
    [
        ([], "at least one"),
        ([1, 2, 3], "power of two"),
        ([-1, 0], "unsigned"),
        ([0.0, 1.0], "integers"),
    ],
)
def test_rejects_invalid_samples(samples: list[object], message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        build_basis_encoded_audio_circuit(samples)  # type: ignore[arg-type]


def test_rejects_insufficient_amplitude_bits() -> None:
    with pytest.raises(ValueError, match="at least 3 bits"):
        build_basis_encoded_audio_circuit([0, 7], amplitude_bits=2)
