"""Regression tests for the primary QRDA paper's worked example."""

from __future__ import annotations

import math

from qiskit.quantum_info import Statevector

from qseb.audio import (
    build_qrda_circuit,
    exact_qrda_probabilities,
    reconstruct_qrda_signal,
    signed_to_unsigned_samples,
    simulate_qrda_counts,
    unsigned_to_signed_samples,
)

PAPER_SIGNED_SAMPLES = (
    0,
    3,
    5,
    7,
    7,
    5,
    3,
    0,
    -3,
    -5,
    -7,
    -7,
    -5,
    -3,
    0,
)

PAPER_UNSIGNED_SAMPLES = (
    8,
    11,
    13,
    15,
    15,
    13,
    11,
    8,
    5,
    3,
    1,
    1,
    3,
    5,
    8,
)


def _build_paper_example():
    unsigned = signed_to_unsigned_samples(
        PAPER_SIGNED_SAMPLES,
        amplitude_bits=4,
    )
    return build_qrda_circuit(unsigned, amplitude_bits=4)


def test_primary_paper_quantization_translation() -> None:
    assert (
        signed_to_unsigned_samples(
            PAPER_SIGNED_SAMPLES,
            amplitude_bits=4,
        )
        == PAPER_UNSIGNED_SAMPLES
    )


def test_primary_paper_register_dimensions() -> None:
    circuit, spec = _build_paper_example()

    assert spec.num_samples == 15
    assert spec.amplitude_bits == 4
    assert spec.time_bits == 4
    assert spec.total_qubits == 8
    assert circuit.num_qubits == 8


def test_primary_paper_qrda_box_metadata() -> None:
    _, spec = _build_paper_example()

    assert spec.box_size == 16
    assert spec.padding_count == 1
    assert math.isclose(spec.padding_fraction, 1 / 16)


def test_primary_paper_exact_support_contains_all_samples_and_padding() -> None:
    circuit, spec = _build_paper_example()
    probabilities = exact_qrda_probabilities(circuit, spec)

    expected = {
        (time_index, amplitude) for time_index, amplitude in enumerate(PAPER_UNSIGNED_SAMPLES)
    }
    expected.add((15, 0))

    assert set(probabilities) == expected
    assert len(probabilities) == 16


def test_primary_paper_each_basis_state_has_probability_one_sixteenth() -> None:
    circuit, spec = _build_paper_example()
    probabilities = exact_qrda_probabilities(circuit, spec)

    for probability in probabilities.values():
        assert math.isclose(probability, 1 / 16, abs_tol=1e-12)


def test_primary_paper_padding_state_is_zero_amplitude() -> None:
    circuit, spec = _build_paper_example()
    probabilities = exact_qrda_probabilities(circuit, spec)

    assert (15, 0) in probabilities
    assert math.isclose(probabilities[(15, 0)], 1 / 16, abs_tol=1e-12)


def test_primary_paper_statevector_has_sixteen_equal_amplitudes() -> None:
    circuit, _ = _build_paper_example()
    statevector = Statevector.from_instruction(circuit)

    nonzero = [amplitude for amplitude in statevector.data if abs(amplitude) > 1e-12]

    assert len(nonzero) == 16

    for amplitude in nonzero:
        assert math.isclose(abs(amplitude), 1 / 4, abs_tol=1e-12)


def test_primary_paper_has_33_set_amplitude_bits() -> None:
    assert sum(value.bit_count() for value in PAPER_UNSIGNED_SAMPLES) == 33


def test_primary_paper_circuit_emits_33_controlled_amplitude_writes() -> None:
    circuit, _ = _build_paper_example()
    operations = circuit.count_ops()

    assert operations.get("mcx", 0) == 33


def test_primary_paper_shot_reconstruction_is_exact() -> None:
    circuit, spec = _build_paper_example()
    counts = simulate_qrda_counts(
        circuit,
        shots=16384,
        seed_simulator=42,
    )

    reconstructed_unsigned = tuple(reconstruct_qrda_signal(counts, spec))
    reconstructed_signed = unsigned_to_signed_samples(
        reconstructed_unsigned,
        amplitude_bits=4,
    )

    assert reconstructed_unsigned == PAPER_UNSIGNED_SAMPLES
    assert reconstructed_signed == PAPER_SIGNED_SAMPLES
