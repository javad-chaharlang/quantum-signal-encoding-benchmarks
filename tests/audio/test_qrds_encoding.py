"""Tests for the QRDS fixed-point numerical layer."""

from fractions import Fraction
from math import isclose

import pytest

from qseb.audio.qrds_encoding import (
    QRDSEncodingSpec,
    QRDSFixedPointSpec,
    build_qrds_circuit,
    exact_qrds_probabilities,
    fixed_point_to_twos_complement,
    twos_complement_to_fixed_point,
)


def test_primary_paper_n7_m4_boundary_example() -> None:
    spec = QRDSFixedPointSpec(integer_bits=4, fractional_bits=3)

    assert spec.amplitude_bits == 8
    assert spec.quantum == Fraction(1, 8)
    assert spec.min_amplitude == Fraction(-127, 8)
    assert spec.max_amplitude == Fraction(127, 8)

    assert (
        fixed_point_to_twos_complement(
            15.875,
            integer_bits=4,
            fractional_bits=3,
        )
        == 0b01111111
    )

    assert (
        fixed_point_to_twos_complement(
            -15.875,
            integer_bits=4,
            fractional_bits=3,
        )
        == 0b10000001
    )


@pytest.mark.parametrize(
    ("value", "expected_code"),
    [
        (2.25, 0b01001),
        (0.75, 0b00011),
        (-1.25, 0b11011),
        (1.50, 0b00110),
        (2.50, 0b01010),
        (-1.00, 0b11100),
    ],
)
def test_compact_primary_paper_signal_codes(
    value: float,
    expected_code: int,
) -> None:
    code = fixed_point_to_twos_complement(
        value,
        integer_bits=2,
        fractional_bits=2,
    )

    assert code == expected_code

    reconstructed = twos_complement_to_fixed_point(
        code,
        integer_bits=2,
        fractional_bits=2,
    )

    assert reconstructed == Fraction(str(value))


@pytest.mark.parametrize(
    "value",
    [
        -3.75,
        -2.50,
        -1.25,
        -0.25,
        0,
        0.25,
        1.50,
        2.25,
        3.75,
    ],
)
def test_fixed_point_round_trip(value: float) -> None:
    code = fixed_point_to_twos_complement(
        value,
        integer_bits=2,
        fractional_bits=2,
    )

    reconstructed = twos_complement_to_fixed_point(
        code,
        integer_bits=2,
        fractional_bits=2,
    )

    assert reconstructed == Fraction(str(value))


def test_reject_non_quantized_amplitude() -> None:
    with pytest.raises(ValueError, match="not aligned"):
        fixed_point_to_twos_complement(
            0.1,
            integer_bits=2,
            fractional_bits=2,
        )


@pytest.mark.parametrize("value", [-4.0, 4.0])
def test_reject_values_outside_primary_paper_range(value: float) -> None:
    with pytest.raises(ValueError, match="outside"):
        fixed_point_to_twos_complement(
            value,
            integer_bits=2,
            fractional_bits=2,
        )


def test_reject_sign_only_most_negative_code() -> None:
    with pytest.raises(ValueError, match="symmetric amplitude range"):
        twos_complement_to_fixed_point(
            0b10000,
            integer_bits=2,
            fractional_bits=2,
        )


def test_reject_invalid_fixed_point_layout() -> None:
    with pytest.raises(ValueError, match="integer_bits"):
        QRDSFixedPointSpec(integer_bits=-1, fractional_bits=2)

    with pytest.raises(ValueError, match="fractional_bits"):
        QRDSFixedPointSpec(integer_bits=2, fractional_bits=-1)


PAPER_COMPACT_SIGNAL = [
    2.25,
    0.75,
    -1.25,
    1.50,
    2.50,
    -1.00,
]


def test_compact_primary_paper_signal_metadata() -> None:
    circuit, spec = build_qrds_circuit(
        PAPER_COMPACT_SIGNAL,
        integer_bits=2,
        fractional_bits=2,
    )

    assert isinstance(spec, QRDSEncodingSpec)
    assert spec.num_samples == 6
    assert spec.integer_bits == 2
    assert spec.fractional_bits == 2
    assert spec.amplitude_bits == 5
    assert spec.position_bits == 3
    assert spec.total_qubits == 8
    assert spec.box_size == 8
    assert spec.padding_count == 2
    assert spec.quantum == Fraction(1, 4)
    assert circuit.num_qubits == 8


def test_compact_primary_paper_signal_exact_state_support() -> None:
    circuit, spec = build_qrds_circuit(
        PAPER_COMPACT_SIGNAL,
        integer_bits=2,
        fractional_bits=2,
    )

    probabilities = exact_qrds_probabilities(circuit, spec)

    expected = {
        (position, Fraction(str(amplitude))): 1 / 8
        for position, amplitude in enumerate(PAPER_COMPACT_SIGNAL)
    }

    expected[(6, Fraction(0, 1))] = 1 / 8
    expected[(7, Fraction(0, 1))] = 1 / 8

    assert set(probabilities) == set(expected)

    for key, expected_probability in expected.items():
        assert isclose(
            probabilities[key],
            expected_probability,
            abs_tol=1e-12,
        )


def test_qrds_padding_positions_remain_zero() -> None:
    circuit, spec = build_qrds_circuit(
        PAPER_COMPACT_SIGNAL,
        integer_bits=2,
        fractional_bits=2,
    )

    probabilities = exact_qrds_probabilities(circuit, spec)

    assert (6, Fraction(0, 1)) in probabilities
    assert (7, Fraction(0, 1)) in probabilities

    assert all(
        amplitude == 0 for position, amplitude in probabilities if position >= spec.num_samples
    )


def test_single_sample_qrds_uses_one_position_qubit() -> None:
    circuit, spec = build_qrds_circuit(
        [1.25],
        integer_bits=2,
        fractional_bits=2,
    )

    assert spec.position_bits == 1
    assert spec.box_size == 2
    assert spec.padding_count == 1
    assert circuit.num_qubits == 6


def test_qrds_circuit_rejects_off_grid_amplitude() -> None:
    with pytest.raises(ValueError, match="not aligned"):
        build_qrds_circuit(
            [0.25, 0.1],
            integer_bits=2,
            fractional_bits=2,
        )
