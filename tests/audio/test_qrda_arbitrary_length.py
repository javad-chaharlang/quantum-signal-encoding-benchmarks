"""Tests for arbitrary-length QRDA 2^l boxes."""

from __future__ import annotations

import math

import pytest

from qseb.audio import (
    build_qrda_circuit,
    exact_qrda_probabilities,
    reconstruct_qrda_signal,
    simulate_qrda_counts,
)


@pytest.mark.parametrize(
    ("samples", "expected_time_bits", "expected_box_size", "expected_padding"),
    [
        ([5], 1, 2, 1),
        ([1, 2, 3], 2, 4, 1),
        ([1, 2, 3, 4, 5], 3, 8, 3),
        (list(range(15)), 4, 16, 1),
        (list(range(16)), 4, 16, 0),
        (list(range(17)), 5, 32, 15),
    ],
)
def test_qrda_box_dimensions_for_arbitrary_lengths(
    samples: list[int],
    expected_time_bits: int,
    expected_box_size: int,
    expected_padding: int,
) -> None:
    circuit, spec = build_qrda_circuit(samples)

    assert circuit.num_qubits == spec.amplitude_bits + expected_time_bits
    assert spec.num_samples == len(samples)
    assert spec.time_bits == expected_time_bits
    assert spec.box_size == expected_box_size
    assert spec.padding_count == expected_padding


def test_three_sample_qrda_contains_zero_amplitude_padding_state() -> None:
    samples = [1, 2, 3]
    circuit, spec = build_qrda_circuit(samples, amplitude_bits=2)
    probabilities = exact_qrda_probabilities(circuit, spec)

    assert set(probabilities) == {
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
    }

    for probability in probabilities.values():
        assert math.isclose(probability, 0.25, abs_tol=1e-12)


def test_five_sample_qrda_contains_three_padding_states() -> None:
    samples = [1, 2, 3, 4, 5]
    circuit, spec = build_qrda_circuit(samples, amplitude_bits=3)
    probabilities = exact_qrda_probabilities(circuit, spec)

    expected_effective = {(time_index, amplitude) for time_index, amplitude in enumerate(samples)}
    expected_padding = {
        (5, 0),
        (6, 0),
        (7, 0),
    }

    assert set(probabilities) == expected_effective | expected_padding

    for probability in probabilities.values():
        assert math.isclose(probability, 1 / 8, abs_tol=1e-12)


def test_single_sample_uses_one_time_qubit_and_one_padding_state() -> None:
    circuit, spec = build_qrda_circuit([5], amplitude_bits=3)
    probabilities = exact_qrda_probabilities(circuit, spec)

    assert spec.time_bits == 1
    assert spec.box_size == 2
    assert spec.padding_count == 1
    assert set(probabilities) == {(0, 5), (1, 0)}
    assert math.isclose(probabilities[(0, 5)], 0.5, abs_tol=1e-12)
    assert math.isclose(probabilities[(1, 0)], 0.5, abs_tol=1e-12)


def test_arbitrary_length_shot_reconstruction_excludes_padding() -> None:
    samples = [1, 2, 3, 4, 5]
    circuit, spec = build_qrda_circuit(samples, amplitude_bits=3)
    counts = simulate_qrda_counts(
        circuit,
        shots=8192,
        seed_simulator=42,
    )

    reconstructed = reconstruct_qrda_signal(counts, spec)

    assert reconstructed == samples
    assert len(reconstructed) == spec.num_samples
