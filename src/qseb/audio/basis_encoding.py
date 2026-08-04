"""Basis-encoded quantum representation of a quantized audio signal.

The prepared state is

    |A> = 1/sqrt(N) sum_t |a_t>_amp |t>_time,

where N is a power of two, ``a_t`` is a non-negative integer amplitude,
and Qiskit little-endian qubit indexing is used inside each register.

This module implements a transparent educational baseline. It is not an
implementation of QRDA, FRQA, or QPAM.
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
class AudioEncodingSpec:
    """Register dimensions and quantization metadata for one encoded signal."""

    num_samples: int
    amplitude_bits: int
    time_bits: int
    min_amplitude: int = 0

    @property
    def total_qubits(self) -> int:
        """Return the total number of data qubits."""

        return self.amplitude_bits + self.time_bits

    @property
    def max_amplitude(self) -> int:
        """Return the maximum unsigned amplitude supported by the register."""

        return (1 << self.amplitude_bits) - 1


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _validate_samples(
    samples: Sequence[int] | Iterable[int],
    amplitude_bits: int | None,
) -> tuple[tuple[int, ...], AudioEncodingSpec]:
    values = tuple(samples)

    if not values:
        raise ValueError("samples must contain at least one value")

    if not _is_power_of_two(len(values)):
        raise ValueError("the number of samples must be a power of two")

    if any(not isinstance(value, Integral) for value in values):
        raise TypeError("all samples must be integers after quantization")

    if any(int(value) < 0 for value in values):
        raise ValueError("basis encoding currently supports unsigned amplitudes only")

    normalized = tuple(int(value) for value in values)
    required_bits = max(1, ceil(log2(max(normalized) + 1)))
    selected_bits = required_bits if amplitude_bits is None else amplitude_bits

    if not isinstance(selected_bits, int) or selected_bits < 1:
        raise ValueError("amplitude_bits must be a positive integer")

    if selected_bits < required_bits:
        raise ValueError(
            f"amplitude_bits={selected_bits} cannot represent maximum sample "
            f"value {max(normalized)}; at least {required_bits} bits are required"
        )

    spec = AudioEncodingSpec(
        num_samples=len(normalized),
        amplitude_bits=selected_bits,
        time_bits=int(log2(len(normalized))),
    )

    return normalized, spec


def build_basis_encoded_audio_circuit(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int | None = None,
    add_barriers: bool = True,
) -> tuple[QuantumCircuit, AudioEncodingSpec]:
    """Build a circuit for a uniformly indexed basis-encoded audio signal.

    Args:
        samples: Unsigned, quantized integer samples. The length must be a power of two.
        amplitude_bits: Optional amplitude-register width. When omitted, the minimum
            sufficient width is selected.
        add_barriers: Insert visual barriers between preparation stages.

    Returns:
        A tuple containing the unmeasured preparation circuit and its encoding spec.

    Notes:
        Amplitude qubit ``i`` stores bit ``i`` of the integer amplitude, and time
        qubit ``i`` stores bit ``i`` of the sample index. Both use little-endian
        indexing. The amplitude register is listed before the time register in the
        circuit, so the computational-basis integer is ``amplitude + (time << m)``.
    """

    values, spec = _validate_samples(samples, amplitude_bits)

    amplitude = QuantumRegister(spec.amplitude_bits, "amplitude")

    if spec.time_bits:
        time = QuantumRegister(spec.time_bits, "time")
        circuit = QuantumCircuit(amplitude, time, name="basis_audio")
        circuit.h(time)
    else:
        time = None
        circuit = QuantumCircuit(amplitude, name="basis_audio")

    if add_barriers:
        circuit.barrier()

    for time_index, sample in enumerate(values):
        zero_controls = [
            qubit_index
            for qubit_index in range(spec.time_bits)
            if ((time_index >> qubit_index) & 1) == 0
        ]

        for qubit_index in zero_controls:
            circuit.x(time[qubit_index])  # type: ignore[index]

        for amplitude_index in range(spec.amplitude_bits):
            if ((sample >> amplitude_index) & 1) == 0:
                continue

            if spec.time_bits == 0:
                circuit.x(amplitude[amplitude_index])
            elif spec.time_bits == 1:
                circuit.cx(
                    time[0],  # type: ignore[index]
                    amplitude[amplitude_index],
                )
            else:
                circuit.mcx(
                    list(time),  # type: ignore[arg-type]
                    amplitude[amplitude_index],
                )

        for qubit_index in reversed(zero_controls):
            circuit.x(time[qubit_index])  # type: ignore[index]

    if add_barriers:
        circuit.barrier()

    return circuit, spec


def exact_basis_probabilities(
    circuit: QuantumCircuit,
    spec: AudioEncodingSpec,
    *,
    atol: float = 1e-12,
) -> dict[tuple[int, int], float]:
    """Return non-zero exact probabilities as ``(time, amplitude) -> probability``."""

    if circuit.num_clbits:
        raise ValueError("exact statevector validation requires an unmeasured circuit")

    if circuit.num_qubits != spec.total_qubits:
        raise ValueError("circuit qubit count does not match the encoding specification")

    probabilities = Statevector.from_instruction(circuit).probabilities()
    decoded: dict[tuple[int, int], float] = {}
    amplitude_mask = (1 << spec.amplitude_bits) - 1

    for basis_index, probability in enumerate(probabilities):
        if probability <= atol:
            continue

        amplitude = basis_index & amplitude_mask
        time_index = basis_index >> spec.amplitude_bits
        decoded[(time_index, amplitude)] = float(probability)

    return decoded


def simulate_counts(
    circuit: QuantumCircuit,
    *,
    shots: int = 4096,
    seed_simulator: int = 42,
    optimization_level: int = 1,
    simulator: AerSimulator | None = None,
) -> dict[str, int]:
    """Measure and simulate an encoding circuit with Qiskit Aer."""

    if shots < 1:
        raise ValueError("shots must be a positive integer")

    if circuit.num_clbits:
        raise ValueError("pass the unmeasured preparation circuit")

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


def decode_measurement_counts(
    counts: Mapping[str, int],
    spec: AudioEncodingSpec,
) -> dict[int, Counter[int]]:
    """Decode Qiskit counts into amplitude frequencies for each time index.

    ``measure_all`` maps classical bit ``i`` to circuit qubit ``i``. Qiskit renders
    count strings from the highest classical bit to the lowest, so each bitstring is
    reversed before amplitude and time fields are extracted.
    """

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

        amplitude = sum(int(bit) << index for index, bit in enumerate(amplitude_bits))
        time_index = sum(int(bit) << index for index, bit in enumerate(time_bits))

        decoded[time_index][amplitude] += int(count)

    return dict(decoded)


def reconstruct_from_counts(
    counts: Mapping[str, int],
    spec: AudioEncodingSpec,
) -> list[int]:
    """Reconstruct one integer amplitude per time index using the modal outcome."""

    decoded = decode_measurement_counts(counts, spec)
    reconstructed: list[int] = []

    for time_index in range(spec.num_samples):
        frequencies = decoded.get(time_index)

        if not frequencies:
            raise ValueError(
                f"no measurement was observed for time index {time_index}; "
                "increase the number of shots"
            )

        # Deterministic tie-break: prefer the lower amplitude.
        amplitude = min(
            frequencies,
            key=lambda value: (-frequencies[value], value),
        )

        reconstructed.append(amplitude)

    return reconstructed


def circuit_resource_metrics(
    circuit: QuantumCircuit,
    *,
    basis_gates: Sequence[str] = ("rz", "sx", "x", "cx"),
    optimization_level: int = 1,
) -> dict[str, object]:
    """Return raw and basis-transpiled circuit resource metrics."""

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
        "basis_gates": tuple(basis_gates),
        "optimization_level": optimization_level,
    }
