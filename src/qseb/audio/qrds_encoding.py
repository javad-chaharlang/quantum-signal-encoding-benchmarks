"""Quantum Representation of Digital Signals (QRDS).

This module begins with the exact fixed-point numerical layer required by the
QRDS representation introduced by Li et al. QRDS stores each signal amplitude
in a signed two's-complement basis register containing:

    1 sign bit + m integer bits + (n - m) fractional bits

The primary paper states a symmetric representable amplitude interval that
excludes the otherwise standard two's-complement value -2^m. This implementation
deliberately follows that stated QRDS convention and the numerical examples in
the paper rather than silently substituting a programming-language convention.

Primary reference:
    Li, P., Wang, B., Xiao, H., & Liu, X. (2018).
    Quantum Representation and Basic Operations of Digital Signals.
    International Journal of Theoretical Physics, 57, 3242-3270.
    https://doi.org/10.1007/s10773-018-3841-0
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import ceil, log2
from numbers import Integral

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


@dataclass(frozen=True, slots=True)
class QRDSFixedPointSpec:
    """Fixed-point amplitude layout used by the QRDS primary paper.

    ``integer_bits`` corresponds to ``m`` in the paper.
    ``fractional_bits`` corresponds to ``n - m``.
    The complete amplitude register therefore contains
    ``1 + integer_bits + fractional_bits`` qubits.
    """

    integer_bits: int
    fractional_bits: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.integer_bits, int)
            or isinstance(self.integer_bits, bool)
            or self.integer_bits < 0
        ):
            raise ValueError("integer_bits must be a non-negative integer")

        if (
            not isinstance(self.fractional_bits, int)
            or isinstance(self.fractional_bits, bool)
            or self.fractional_bits < 0
        ):
            raise ValueError("fractional_bits must be a non-negative integer")

    @property
    def magnitude_bits(self) -> int:
        """Return n, the number of non-sign amplitude bits."""

        return self.integer_bits + self.fractional_bits

    @property
    def amplitude_bits(self) -> int:
        """Return the complete QRDS amplitude-register width, n + 1."""

        return self.magnitude_bits + 1

    @property
    def scale(self) -> int:
        """Return the integer scaling factor for exact fixed-point conversion."""

        return 1 << self.fractional_bits

    @property
    def quantum(self) -> Fraction:
        """Return the smallest representable amplitude increment."""

        return Fraction(1, self.scale)

    @property
    def min_amplitude(self) -> Fraction:
        """Return the minimum amplitude stated by the QRDS primary paper."""

        return Fraction(-(1 << self.magnitude_bits) + 1, self.scale)

    @property
    def max_amplitude(self) -> Fraction:
        """Return the maximum amplitude stated by the QRDS primary paper."""

        return Fraction((1 << self.magnitude_bits) - 1, self.scale)

    @property
    def sign_mask(self) -> int:
        """Return the mask of the sign qubit."""

        return 1 << self.magnitude_bits

    @property
    def max_code(self) -> int:
        """Return the largest basis-state code in the amplitude register."""

        return (1 << self.amplitude_bits) - 1


def _as_fraction(value: int | float | Decimal | Fraction) -> Fraction:
    """Convert a supported classical value to an exact rational number."""

    if isinstance(value, bool):
        raise TypeError("value must be a real numeric amplitude")

    if isinstance(value, Integral):
        return Fraction(int(value), 1)

    if isinstance(value, Fraction):
        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("value must be finite")
        return Fraction(value)

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("value must be finite")
        return Fraction(str(value))

    raise TypeError("value must be an int, float, Decimal, or Fraction")


def fixed_point_to_twos_complement(
    value: int | float | Decimal | Fraction,
    *,
    integer_bits: int,
    fractional_bits: int,
) -> int:
    """Encode one QRDS fixed-point amplitude as a two's-complement basis code."""

    spec = QRDSFixedPointSpec(
        integer_bits=integer_bits,
        fractional_bits=fractional_bits,
    )
    amplitude = _as_fraction(value)

    if amplitude < spec.min_amplitude or amplitude > spec.max_amplitude:
        raise ValueError(
            f"value {amplitude} is outside the QRDS paper range "
            f"[{spec.min_amplitude}, {spec.max_amplitude}]"
        )

    scaled = amplitude * spec.scale
    if scaled.denominator != 1:
        raise ValueError(
            f"value {amplitude} is not aligned to the QRDS fixed-point quantum {spec.quantum}"
        )

    scaled_integer = scaled.numerator
    if scaled_integer >= 0:
        return scaled_integer

    return (1 << spec.amplitude_bits) + scaled_integer


def twos_complement_to_fixed_point(
    code: int,
    *,
    integer_bits: int,
    fractional_bits: int,
) -> Fraction:
    """Decode a QRDS two's-complement basis code to an exact amplitude."""

    spec = QRDSFixedPointSpec(
        integer_bits=integer_bits,
        fractional_bits=fractional_bits,
    )

    if not isinstance(code, Integral) or isinstance(code, bool):
        raise TypeError("code must be an integer")

    code = int(code)
    if code < 0 or code > spec.max_code:
        raise ValueError(
            f"code must lie in [0, {spec.max_code}] for amplitude_bits={spec.amplitude_bits}"
        )

    scaled_integer = code - (1 << spec.amplitude_bits) if code & spec.sign_mask else code

    amplitude = Fraction(scaled_integer, spec.scale)

    # The standard two's-complement sign-only pattern would encode -2^m.
    # The QRDS primary paper instead states the symmetric lower endpoint
    # -2^m + 2^-(n-m), so that single pattern is outside the paper domain.
    if amplitude < spec.min_amplitude:
        raise ValueError(
            f"code {code} represents {amplitude}, which is outside "
            "the symmetric amplitude range stated by the QRDS paper"
        )

    return amplitude


@dataclass(frozen=True, slots=True)
class QRDSEncodingSpec:
    """Register dimensions and padding metadata for one QRDS signal."""

    num_samples: int
    integer_bits: int
    fractional_bits: int
    position_bits: int

    @property
    def amplitude_bits(self) -> int:
        """Return the full fixed-point amplitude-register width."""

        return 1 + self.integer_bits + self.fractional_bits

    @property
    def total_qubits(self) -> int:
        """Return amplitude plus position qubits."""

        return self.amplitude_bits + self.position_bits

    @property
    def box_size(self) -> int:
        """Return the represented number of positions, 2^k."""

        return 1 << self.position_bits

    @property
    def padding_count(self) -> int:
        """Return the number of redundant zero-amplitude positions."""

        return self.box_size - self.num_samples

    @property
    def quantum(self) -> Fraction:
        """Return the fixed-point amplitude resolution."""

        return Fraction(1, 1 << self.fractional_bits)

    @property
    def min_amplitude(self) -> Fraction:
        """Return the lower endpoint stated by the QRDS paper."""

        magnitude_bits = self.integer_bits + self.fractional_bits
        scale = 1 << self.fractional_bits
        return Fraction(-(1 << magnitude_bits) + 1, scale)

    @property
    def max_amplitude(self) -> Fraction:
        """Return the upper endpoint stated by the QRDS paper."""

        magnitude_bits = self.integer_bits + self.fractional_bits
        scale = 1 << self.fractional_bits
        return Fraction((1 << magnitude_bits) - 1, scale)


def _position_bits_for_length(num_samples: int) -> int:
    """Return the QRDS position-register width k."""

    if not isinstance(num_samples, int) or isinstance(num_samples, bool):
        raise TypeError("num_samples must be an integer")

    if num_samples < 1:
        raise ValueError("num_samples must be positive")

    # Keep one physical position qubit for the one-sample implementation case.
    if num_samples == 1:
        return 1

    return ceil(log2(num_samples))


def _validate_qrds_samples(
    samples: Sequence[int | float | Decimal | Fraction]
    | Iterable[int | float | Decimal | Fraction],
    *,
    integer_bits: int,
    fractional_bits: int,
) -> tuple[tuple[Fraction, ...], QRDSEncodingSpec]:
    """Validate amplitudes and construct a QRDS encoding specification."""

    values = tuple(samples)

    if not values:
        raise ValueError("samples must contain at least one value")

    fixed_spec = QRDSFixedPointSpec(
        integer_bits=integer_bits,
        fractional_bits=fractional_bits,
    )

    normalized: list[Fraction] = []

    for value in values:
        amplitude = _as_fraction(value)

        # Encoding performs both range and fixed-point-grid validation.
        fixed_point_to_twos_complement(
            amplitude,
            integer_bits=integer_bits,
            fractional_bits=fractional_bits,
        )

        normalized.append(amplitude)

    spec = QRDSEncodingSpec(
        num_samples=len(normalized),
        integer_bits=fixed_spec.integer_bits,
        fractional_bits=fixed_spec.fractional_bits,
        position_bits=_position_bits_for_length(len(normalized)),
    )

    return tuple(normalized), spec


def build_qrds_circuit(
    samples: Sequence[int | float | Decimal | Fraction]
    | Iterable[int | float | Decimal | Fraction],
    *,
    integer_bits: int,
    fractional_bits: int,
    add_barriers: bool = True,
) -> tuple[QuantumCircuit, QRDSEncodingSpec]:
    """Build the minimal QRDS state-preparation circuit.

    The position register is placed into an equal superposition and each
    effective signal sample is written into the fixed-point amplitude register
    under control of its position basis state. Redundant positions remain at
    zero amplitude.
    """

    values, spec = _validate_qrds_samples(
        samples,
        integer_bits=integer_bits,
        fractional_bits=fractional_bits,
    )

    amplitude = QuantumRegister(spec.amplitude_bits, "amplitude")
    position = QuantumRegister(spec.position_bits, "position")

    circuit = QuantumCircuit(
        amplitude,
        position,
        name="qrds_signal",
    )

    # QRDS preparation step 1: equal superposition of all 2^k positions.
    circuit.h(position)

    if add_barriers:
        circuit.barrier()

    # QRDS preparation step 2: conditionally set the amplitude basis word
    # associated with each effective position.
    for position_index, sample in enumerate(values):
        code = fixed_point_to_twos_complement(
            sample,
            integer_bits=spec.integer_bits,
            fractional_bits=spec.fractional_bits,
        )

        zero_controls = [
            qubit_index
            for qubit_index in range(spec.position_bits)
            if ((position_index >> qubit_index) & 1) == 0
        ]

        for qubit_index in zero_controls:
            circuit.x(position[qubit_index])

        for amplitude_index in range(spec.amplitude_bits):
            if ((code >> amplitude_index) & 1) == 0:
                continue

            if spec.position_bits == 1:
                circuit.cx(
                    position[0],
                    amplitude[amplitude_index],
                )
            else:
                circuit.mcx(
                    list(position),
                    amplitude[amplitude_index],
                )

        for qubit_index in reversed(zero_controls):
            circuit.x(position[qubit_index])

    if add_barriers:
        circuit.barrier()

    return circuit, spec


def exact_qrds_probabilities(
    circuit: QuantumCircuit,
    spec: QRDSEncodingSpec,
    *,
    atol: float = 1e-12,
) -> dict[tuple[int, Fraction], float]:
    """Return non-zero QRDS probabilities indexed by position and amplitude."""

    if circuit.num_clbits:
        raise ValueError("exact statevector validation requires an unmeasured circuit")

    if circuit.num_qubits != spec.total_qubits:
        raise ValueError("circuit qubit count does not match the QRDS specification")

    probabilities = Statevector.from_instruction(circuit).probabilities()

    decoded: dict[tuple[int, Fraction], float] = {}
    amplitude_mask = (1 << spec.amplitude_bits) - 1

    for basis_index, probability in enumerate(probabilities):
        if probability <= atol:
            continue

        code = basis_index & amplitude_mask
        position_index = basis_index >> spec.amplitude_bits

        amplitude = twos_complement_to_fixed_point(
            code,
            integer_bits=spec.integer_bits,
            fractional_bits=spec.fractional_bits,
        )

        decoded[(position_index, amplitude)] = float(probability)

    return decoded


def simulate_qrds_counts(
    circuit: QuantumCircuit,
    *,
    shots: int = 4096,
    seed_simulator: int = 42,
    optimization_level: int = 1,
    simulator: AerSimulator | None = None,
) -> dict[str, int]:
    """Measure and simulate an unmeasured QRDS preparation circuit."""

    if shots < 1:
        raise ValueError("shots must be a positive integer")

    if circuit.num_clbits:
        raise ValueError("pass the unmeasured QRDS preparation circuit")

    backend = simulator or AerSimulator()
    measured = circuit.measure_all(inplace=False)

    compiled = transpile(
        measured,
        backend,
        optimization_level=optimization_level,
    )

    result = backend.run(
        compiled,
        shots=shots,
        seed_simulator=seed_simulator,
    ).result()

    return dict(result.get_counts())


def decode_qrds_counts(
    counts: Mapping[str, int],
    spec: QRDSEncodingSpec,
) -> dict[int, Counter[Fraction]]:
    """Decode Qiskit counts into amplitude frequencies for each position."""

    decoded: dict[int, Counter[Fraction]] = defaultdict(Counter)
    expected_width = spec.total_qubits

    for raw_bitstring, count in counts.items():
        compact = raw_bitstring.replace(" ", "")

        if len(compact) != expected_width:
            raise ValueError(
                f"bitstring {raw_bitstring!r} has width {len(compact)}; expected {expected_width}"
            )

        if set(compact) - {"0", "1"}:
            raise ValueError(f"invalid measurement bitstring: {raw_bitstring!r}")

        if count < 0:
            raise ValueError("measurement counts cannot be negative")

        qubit_order = compact[::-1]

        amplitude_bits = qubit_order[: spec.amplitude_bits]
        position_bits = qubit_order[spec.amplitude_bits :]

        code = sum(int(bit) << index for index, bit in enumerate(amplitude_bits))

        position_index = sum(int(bit) << index for index, bit in enumerate(position_bits))

        amplitude = twos_complement_to_fixed_point(
            code,
            integer_bits=spec.integer_bits,
            fractional_bits=spec.fractional_bits,
        )

        decoded[position_index][amplitude] += int(count)

    return dict(decoded)


def reconstruct_qrds_signal(
    counts: Mapping[str, int],
    spec: QRDSEncodingSpec,
) -> list[Fraction]:
    """Reconstruct the effective QRDS signal from measurement counts."""

    decoded = decode_qrds_counts(counts, spec)
    reconstructed: list[Fraction] = []

    for position_index in range(spec.num_samples):
        frequencies = decoded.get(position_index)

        if not frequencies:
            raise ValueError(
                f"no measurement was observed for effective position "
                f"{position_index}; increase the number of shots"
            )

        amplitude = min(
            frequencies,
            key=lambda value: (
                -frequencies[value],
                value,
            ),
        )

        reconstructed.append(amplitude)

    return reconstructed


def qrds_resource_metrics(
    circuit: QuantumCircuit,
    *,
    basis_gates: Sequence[str] = ("rz", "sx", "x", "cx"),
    optimization_level: int = 1,
) -> dict[str, object]:
    """Return raw and basis-transpiled QRDS circuit resource metrics."""

    compiled = transpile(
        circuit,
        basis_gates=list(basis_gates),
        optimization_level=optimization_level,
    )

    return {
        "num_qubits": circuit.num_qubits,
        "raw_depth": circuit.depth(),
        "raw_size": circuit.size(),
        "raw_operations": dict(circuit.count_ops()),
        "transpiled_depth": compiled.depth(),
        "transpiled_size": compiled.size(),
        "transpiled_operations": dict(compiled.count_ops()),
    }


__all__ = [
    "QRDSEncodingSpec",
    "QRDSFixedPointSpec",
    "build_qrds_circuit",
    "decode_qrds_counts",
    "exact_qrds_probabilities",
    "fixed_point_to_twos_complement",
    "qrds_resource_metrics",
    "reconstruct_qrds_signal",
    "simulate_qrds_counts",
    "twos_complement_to_fixed_point",
]
