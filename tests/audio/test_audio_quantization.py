"""Tests for QRDA signed/unsigned audio translation."""

import pytest

from qseb.audio import (
    qrda_offset,
    signed_amplitude_range,
    signed_to_unsigned_samples,
    unsigned_amplitude_range,
    unsigned_to_signed_samples,
    validate_signed_samples,
    validate_unsigned_samples,
)


PAPER_SIGNED_SAMPLES = (0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0)

PAPER_UNSIGNED_SAMPLES = (8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8)


def test_four_bit_ranges_match_primary_paper() -> None:
    assert signed_amplitude_range(4) == (-8, 7)
    assert unsigned_amplitude_range(4) == (0, 15)
    assert qrda_offset(4) == 8


def test_primary_paper_signed_to_unsigned_example() -> None:
    assert (
        signed_to_unsigned_samples(PAPER_SIGNED_SAMPLES, amplitude_bits=4) == PAPER_UNSIGNED_SAMPLES
    )


def test_primary_paper_unsigned_to_signed_example() -> None:
    assert (
        unsigned_to_signed_samples(PAPER_UNSIGNED_SAMPLES, amplitude_bits=4) == PAPER_SIGNED_SAMPLES
    )


def test_primary_paper_round_trip_is_exact() -> None:
    unsigned = signed_to_unsigned_samples(PAPER_SIGNED_SAMPLES, amplitude_bits=4)
    assert unsigned_to_signed_samples(unsigned, amplitude_bits=4) == PAPER_SIGNED_SAMPLES


@pytest.mark.parametrize(
    ("signed_value", "unsigned_value"),
    [(-8, 0), (-7, 1), (-1, 7), (0, 8), (1, 9), (6, 14), (7, 15)],
)
def test_four_bit_reference_values(
    signed_value: int,
    unsigned_value: int,
) -> None:
    assert signed_to_unsigned_samples([signed_value], amplitude_bits=4) == (unsigned_value,)
    assert unsigned_to_signed_samples([unsigned_value], amplitude_bits=4) == (signed_value,)


@pytest.mark.parametrize("value", [-9, 8])
def test_signed_range_rejects_out_of_range_samples(value: int) -> None:
    with pytest.raises(ValueError, match="signed sample"):
        validate_signed_samples([value], amplitude_bits=4)


@pytest.mark.parametrize("value", [-1, 16])
def test_unsigned_range_rejects_out_of_range_samples(value: int) -> None:
    with pytest.raises(ValueError, match="unsigned sample"):
        validate_unsigned_samples([value], amplitude_bits=4)


def test_quantization_rejects_non_integer_samples() -> None:
    with pytest.raises(TypeError, match="integers"):
        signed_to_unsigned_samples([0, 1.5], amplitude_bits=4)


def test_quantization_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one"):
        signed_to_unsigned_samples([], amplitude_bits=4)


@pytest.mark.parametrize("amplitude_bits", [0, -1])
def test_quantization_rejects_nonpositive_width(amplitude_bits: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        signed_amplitude_range(amplitude_bits)


def test_quantization_rejects_boolean_width() -> None:
    with pytest.raises(TypeError, match="integer"):
        qrda_offset(True)
