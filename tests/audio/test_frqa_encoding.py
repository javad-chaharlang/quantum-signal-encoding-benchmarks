"""Tests for the minimal FRQA signed-audio baseline."""

from math import isclose

import pytest

from qseb.audio.frqa_encoding import (
    build_frqa_circuit,
    exact_frqa_probabilities,
    reconstruct_frqa_signal,
    signed_to_twos_complement,
    simulate_frqa_counts,
    twos_complement_to_signed,
)

PAPER_EXAMPLE = [0, 1, 0, -1, 0, 2, 3, 1, -1, -2, -1, 0, 0]


def test_three_bit_twos_complement_round_trip() -> None:
    expected_codes = {
        -4: 0b100,
        -3: 0b101,
        -2: 0b110,
        -1: 0b111,
        0: 0b000,
        1: 0b001,
        2: 0b010,
        3: 0b011,
    }

    for value, code in expected_codes.items():
        assert signed_to_twos_complement(value, 3) == code
        assert twos_complement_to_signed(code, 3) == value


def test_primary_paper_figure_one_metadata() -> None:
    circuit, spec = build_frqa_circuit(PAPER_EXAMPLE, amplitude_bits=3)

    assert spec.num_samples == 13
    assert spec.amplitude_bits == 3
    assert spec.time_bits == 4
    assert spec.total_qubits == 7
    assert spec.box_size == 16
    assert spec.padding_count == 3
    assert circuit.num_qubits == 7


def test_primary_paper_figure_one_exact_state_support() -> None:
    circuit, spec = build_frqa_circuit(PAPER_EXAMPLE, amplitude_bits=3)
    probabilities = exact_frqa_probabilities(circuit, spec)

    expected = {
        (time_index, amplitude): 1 / 16 for time_index, amplitude in enumerate(PAPER_EXAMPLE)
    }
    expected.update({(13, 0): 1 / 16, (14, 0): 1 / 16, (15, 0): 1 / 16})

    assert set(probabilities) == set(expected)
    for key, expected_probability in expected.items():
        assert isclose(probabilities[key], expected_probability, abs_tol=1e-12)


def test_primary_paper_example_shot_reconstruction() -> None:
    circuit, spec = build_frqa_circuit(PAPER_EXAMPLE, amplitude_bits=3)
    counts = simulate_frqa_counts(circuit, shots=4096, seed_simulator=42)

    assert reconstruct_frqa_signal(counts, spec) == PAPER_EXAMPLE


def test_automatic_signed_width() -> None:
    _, spec = build_frqa_circuit([-4, -1, 0, 3], add_barriers=False)
    assert spec.amplitude_bits == 3


def test_single_sample_uses_one_time_qubit() -> None:
    _, spec = build_frqa_circuit([-1], amplitude_bits=2)
    assert spec.time_bits == 1
    assert spec.box_size == 2
    assert spec.padding_count == 1


def test_reject_out_of_range_amplitude() -> None:
    with pytest.raises(ValueError, match="supports"):
        build_frqa_circuit([-5, 0, 3], amplitude_bits=3)


def test_reject_empty_signal() -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_frqa_circuit([])


def test_reject_non_integer_signal() -> None:
    with pytest.raises(TypeError, match="integers"):
        build_frqa_circuit([0, 1.5, -1])


def test_local_sample_modification_changes_only_target_time_index():
    from qseb.audio import build_frqa_circuit, exact_frqa_probabilities

    original = [0, 1, 0, -1, 0, 2, 3, 1, -1, -2, -1, 0, 0]
    modified = original.copy()
    modified[5] = 3

    original_circuit, original_spec = build_frqa_circuit(
        original,
        amplitude_bits=3,
    )
    modified_circuit, modified_spec = build_frqa_circuit(
        modified,
        amplitude_bits=3,
    )

    original_probabilities = exact_frqa_probabilities(
        original_circuit,
        original_spec,
    )
    modified_probabilities = exact_frqa_probabilities(
        modified_circuit,
        modified_spec,
    )

    keys = set(original_probabilities) | set(modified_probabilities)
    atol = 1e-12

    changed_times = {
        time_index
        for time_index, amplitude in keys
        if abs(
            original_probabilities.get((time_index, amplitude), 0.0)
            - modified_probabilities.get((time_index, amplitude), 0.0)
        )
        > atol
    }

    assert changed_times == {5}


def test_local_sample_modification_round_trip_is_local():
    from qseb.audio import (
        build_frqa_circuit,
        reconstruct_frqa_signal,
        simulate_frqa_counts,
    )

    original = [0, 1, 0, -1, 0, 2, 3, 1, -1, -2, -1, 0, 0]
    modified = original.copy()
    modified[5] = 3

    circuit, spec = build_frqa_circuit(
        modified,
        amplitude_bits=3,
    )

    counts = simulate_frqa_counts(
        circuit,
        shots=65536,
        seed_simulator=42,
    )

    reconstructed = reconstruct_frqa_signal(counts, spec)

    assert reconstructed == modified

    changed_indices = [
        index
        for index, (before, after) in enumerate(zip(original, reconstructed, strict=True))
        if before != after
    ]

    assert changed_indices == [5]
