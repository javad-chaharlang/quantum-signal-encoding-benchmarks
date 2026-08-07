"""Quantization helpers for QRDA audio preprocessing."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from numbers import Integral


def _validate_amplitude_bits(amplitude_bits: int) -> int:
    if not isinstance(amplitude_bits, int) or isinstance(amplitude_bits, bool):
        raise TypeError("amplitude_bits must be an integer")
    if amplitude_bits < 1:
        raise ValueError("amplitude_bits must be a positive integer")
    return amplitude_bits


def signed_amplitude_range(amplitude_bits: int) -> tuple[int, int]:
    bits = _validate_amplitude_bits(amplitude_bits)
    offset = 1 << (bits - 1)
    return -offset, offset - 1


def unsigned_amplitude_range(amplitude_bits: int) -> tuple[int, int]:
    bits = _validate_amplitude_bits(amplitude_bits)
    return 0, (1 << bits) - 1


def qrda_offset(amplitude_bits: int) -> int:
    bits = _validate_amplitude_bits(amplitude_bits)
    return 1 << (bits - 1)


def _normalize_integer_samples(
    samples: Sequence[int] | Iterable[int],
) -> tuple[int, ...]:
    values = tuple(samples)
    if not values:
        raise ValueError("samples must contain at least one value")
    if any(not isinstance(value, Integral) for value in values):
        raise TypeError("all samples must be integers after quantization")
    return tuple(int(value) for value in values)


def validate_signed_samples(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int,
) -> tuple[int, ...]:
    values = _normalize_integer_samples(samples)
    minimum, maximum = signed_amplitude_range(amplitude_bits)
    for value in values:
        if value < minimum or value > maximum:
            raise ValueError(
                f"signed sample {value} is outside the {amplitude_bits}-bit "
                f"range [{minimum}, {maximum}]"
            )
    return values


def validate_unsigned_samples(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int,
) -> tuple[int, ...]:
    values = _normalize_integer_samples(samples)
    minimum, maximum = unsigned_amplitude_range(amplitude_bits)
    for value in values:
        if value < minimum or value > maximum:
            raise ValueError(
                f"unsigned sample {value} is outside the {amplitude_bits}-bit "
                f"range [{minimum}, {maximum}]"
            )
    return values


def signed_to_unsigned_samples(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int,
) -> tuple[int, ...]:
    values = validate_signed_samples(samples, amplitude_bits=amplitude_bits)
    offset = qrda_offset(amplitude_bits)
    return tuple(value + offset for value in values)


def unsigned_to_signed_samples(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int,
) -> tuple[int, ...]:
    values = validate_unsigned_samples(samples, amplitude_bits=amplitude_bits)
    offset = qrda_offset(amplitude_bits)
    return tuple(value - offset for value in values)


__all__ = [
    "qrda_offset",
    "signed_amplitude_range",
    "signed_to_unsigned_samples",
    "unsigned_amplitude_range",
    "unsigned_to_signed_samples",
    "validate_signed_samples",
    "validate_unsigned_samples",
]
