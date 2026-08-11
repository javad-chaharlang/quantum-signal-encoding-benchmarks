"""Flexible Representation of Quantum Audio (FRQA).

This module implements the FRQA state representation introduced by Yan et al.:

    |A> = 1/sqrt(2^l) sum_t |S_t>_amp |t>_time

where |S_t> is the q-qubit two's-complement representation of a signed audio
sample and |t> is the l-qubit time index. For signal lengths that are not powers
of two, the unused time positions are retained with zero amplitude, matching the
paper's redundant-state convention.

The implementation intentionally provides only the minimal representation,
preparation, validation, measurement, and reconstruction layer needed for the
repository's QRDA/FRQA comparison. Paper-specific audio operations such as
addition, inversion, delay, and reversal are deliberately deferred unless a
later information-hiding experiment requires them.

Primary reference:
    Yan, F., Iliyasu, A. M., Guo, Y., & Yang, H. (2018).
    Flexible representation and manipulation of audio signals on quantum computers.
    Theoretical Computer Science, 752, 71-85.
    https://doi.org/10.1016/j.tcs.2017.12.025
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import ceil, log2
from numbers import Integral

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


@dataclass(frozen=True, slots=True)
class FRQAEncodingSpec:
    """Register dimensions and redundant-state metadata for one FRQA signal."""

    num_samples: int
    amplitude_bits: int
    time_bits: int

    @property
    def total_qubits(self) -> int:
        """Return the total number of FRQA data qubits."""
        return self.amplitude_bits + self.time_bits

    @property
    def min_amplitude(self) -> int:
        """Return the minimum q-bit two's-complement amplitude."""
        return -(1 << (self.amplitude_bits - 1))

    @property
    def max_amplitude(self) -> int:
        """Return the maximum q-bit two's-complement amplitude."""
        return (1 << (self.amplitude_bits - 1)) - 1

    @property
    def box_size(self) -> int:
        """Return the number of represented time positions, 2^l."""
        return 1 << self.time_bits

    @property
    def padding_count(self) -> int:
        """Return the number of redundant FRQA time positions."""
        return self.box_size - self.num_samples


def _time_bits_for_length(num_samples: int) -> int:
    """Return the FRQA time-register width from Eq. (6) of the primary paper."""
    if num_samples < 1:
        raise ValueError("num_samples must be positive")
    if num_samples == 1:
        return 1
    return ceil(log2(num_samples))


def signed_to_twos_complement(value: int, bits: int) -> int:
    """Encode one signed integer as an unsigned q-bit two's-complement code."""
    if not isinstance(value, Integral):
        raise TypeError("value must be an integer")
    if not isinstance(bits, int) or bits < 1:
        raise ValueError("bits must be a positive integer")

    value = int(value)
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if value < minimum or value > maximum:
        raise ValueError(
            f"value {value} is outside the signed {bits}-bit range [{minimum}, {maximum}]"
        )

    return value if value >= 0 else (1 << bits) + value


def twos_complement_to_signed(code: int, bits: int) -> int:
    """Decode one q-bit two's-complement code into its signed integer value."""
    if not isinstance(code, Integral):
        raise TypeError("code must be an integer")
    if not isinstance(bits, int) or bits < 1:
        raise ValueError("bits must be a positive integer")

    code = int(code)
    maximum_code = (1 << bits) - 1
    if code < 0 or code > maximum_code:
        raise ValueError(f"code must lie in [0, {maximum_code}] for bits={bits}")

    sign_mask = 1 << (bits - 1)
    return code - (1 << bits) if code & sign_mask else code


def _required_signed_bits(values: Sequence[int]) -> int:
    """Return the minimum two's-complement width capable of storing all values."""
    bits = 1
    minimum = min(values)
    maximum = max(values)

    while minimum < -(1 << (bits - 1)) or maximum > (1 << (bits - 1)) - 1:
        bits += 1

    return bits


def _validate_frqa_samples(
    samples: Sequence[int] | Iterable[int],
    amplitude_bits: int | None,
) -> tuple[tuple[int, ...], FRQAEncodingSpec]:
    """Validate signed samples and construct their FRQA encoding specification."""
    values = tuple(samples)

    if not values:
        raise ValueError("samples must contain at least one value")

    if any(not isinstance(value, Integral) for value in values):
        raise TypeError("all samples must be integers after quantization")

    normalized = tuple(int(value) for value in values)
    required_bits = _required_signed_bits(normalized)
    selected_bits = required_bits if amplitude_bits is None else amplitude_bits

    if not isinstance(selected_bits, int) or selected_bits < 1:
        raise ValueError("amplitude_bits must be a positive integer")

    minimum = -(1 << (selected_bits - 1))
    maximum = (1 << (selected_bits - 1)) - 1
    if min(normalized) < minimum or max(normalized) > maximum:
        raise ValueError(
            f"amplitude_bits={selected_bits} supports [{minimum}, {maximum}] but "
            f"samples span [{min(normalized)}, {max(normalized)}]"
        )

    spec = FRQAEncodingSpec(
        num_samples=len(normalized),
        amplitude_bits=selected_bits,
        time_bits=_time_bits_for_length(len(normalized)),
    )
    return normalized, spec


def build_frqa_circuit(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int | None = None,
    add_barriers: bool = True,
) -> tuple[QuantumCircuit, FRQAEncodingSpec]:
    """Build a minimal FRQA preparation circuit for signed quantized audio samples.

    The input API accepts signed integers directly. Each sample is converted to
    its q-bit two's-complement code and then written into the amplitude register
    under control of its time-register basis state.
    """
    values, spec = _validate_frqa_samples(samples, amplitude_bits)

    amplitude = QuantumRegister(spec.amplitude_bits, "amplitude")
    time = QuantumRegister(spec.time_bits, "time")
    circuit = QuantumCircuit(amplitude, time, name="frqa_audio")

    # Eq. (11): initialize a uniform superposition of all 2^l time positions.
    circuit.h(time)

    if add_barriers:
        circuit.barrier()

    # Eqs. (12)-(14): conditionally write each sample's two's-complement code.
    for time_index, sample in enumerate(values):
        code = signed_to_twos_complement(sample, spec.amplitude_bits)
        zero_controls = [
            qubit_index
            for qubit_index in range(spec.time_bits)
            if ((time_index >> qubit_index) & 1) == 0
        ]

        for qubit_index in zero_controls:
            circuit.x(time[qubit_index])

        for amplitude_index in range(spec.amplitude_bits):
            if ((code >> amplitude_index) & 1) == 0:
                continue

            if spec.time_bits == 1:
                circuit.cx(time[0], amplitude[amplitude_index])
            else:
                circuit.mcx(list(time), amplitude[amplitude_index])

        for qubit_index in reversed(zero_controls):
            circuit.x(time[qubit_index])

    if add_barriers:
        circuit.barrier()

    return circuit, spec


def exact_frqa_probabilities(
    circuit: QuantumCircuit,
    spec: FRQAEncodingSpec,
    *,
    atol: float = 1e-12,
) -> dict[tuple[int, int], float]:
    """Return non-zero FRQA probabilities as (time, signed_amplitude) -> probability."""
    if circuit.num_clbits:
        raise ValueError("exact statevector validation requires an unmeasured circuit")

    if circuit.num_qubits != spec.total_qubits:
        raise ValueError("circuit qubit count does not match the FRQA specification")

    probabilities = Statevector.from_instruction(circuit).probabilities()
    decoded: dict[tuple[int, int], float] = {}
    amplitude_mask = (1 << spec.amplitude_bits) - 1

    for basis_index, probability in enumerate(probabilities):
        if probability <= atol:
            continue

        code = basis_index & amplitude_mask
        time_index = basis_index >> spec.amplitude_bits
        amplitude = twos_complement_to_signed(code, spec.amplitude_bits)
        decoded[(time_index, amplitude)] = float(probability)

    return decoded


def simulate_frqa_counts(
    circuit: QuantumCircuit,
    *,
    shots: int = 4096,
    seed_simulator: int = 42,
    optimization_level: int = 1,
    simulator: AerSimulator | None = None,
) -> dict[str, int]:
    """Measure and simulate an unmeasured FRQA preparation circuit with Qiskit Aer."""
    if shots < 1:
        raise ValueError("shots must be a positive integer")

    if circuit.num_clbits:
        raise ValueError("pass the unmeasured FRQA preparation circuit")

    backend = simulator or AerSimulator()
    measured = circuit.measure_all(inplace=False)
    compiled = transpile(measured, backend, optimization_level=optimization_level)
    result = backend.run(compiled, shots=shots, seed_simulator=seed_simulator).result()
    return dict(result.get_counts())


def decode_frqa_counts(
    counts: Mapping[str, int],
    spec: FRQAEncodingSpec,
) -> dict[int, Counter[int]]:
    """Decode Qiskit counts into signed-amplitude frequencies for each time index."""
    decoded: dict[int, Counter[int]] = defaultdict(Counter)
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
        time_bits = qubit_order[spec.amplitude_bits :]

        code = sum(int(bit) << index for index, bit in enumerate(amplitude_bits))
        time_index = sum(int(bit) << index for index, bit in enumerate(time_bits))
        amplitude = twos_complement_to_signed(code, spec.amplitude_bits)
        decoded[time_index][amplitude] += int(count)

    return dict(decoded)


def reconstruct_frqa_signal(
    counts: Mapping[str, int],
    spec: FRQAEncodingSpec,
) -> list[int]:
    """Reconstruct only the L effective FRQA samples using modal amplitudes."""
    decoded = decode_frqa_counts(counts, spec)
    reconstructed: list[int] = []

    for time_index in range(spec.num_samples):
        frequencies = decoded.get(time_index)

        if not frequencies:
            raise ValueError(
                f"no measurement was observed for effective time index {time_index}; "
                "increase the number of shots"
            )

        amplitude = min(
            frequencies,
            key=lambda value: (-frequencies[value], value),
        )
        reconstructed.append(amplitude)

    return reconstructed


__all__ = [
    "FRQAEncodingSpec",
    "build_frqa_circuit",
    "decode_frqa_counts",
    "exact_frqa_probabilities",
    "reconstruct_frqa_signal",
    "signed_to_twos_complement",
    "simulate_frqa_counts",
    "twos_complement_to_signed",
]
