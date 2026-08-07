"""Quantum Representation of Digital Audio (QRDA).

This module implements the QRDA state representation described by Jian Wang:

    |B> = 1/sqrt(2^l) [
        sum_{T=0}^{L-1} |D_T>_amp |T>_time
        + sum_{T=L}^{2^l-1} |0>^q |T>_time
    ]

where:
- L is the number of effective audio samples,
- q is the amplitude-register width,
- l = ceil(log2(L)) for L > 1 and l = 1 for L = 1,
- the remaining 2^l - L time positions are QRDA padding states with zero amplitude.

The implementation uses unsigned integer amplitudes, matching the QRDA paper after
its signed-to-unsigned translation. Signed/unsigned conversion is added separately
in the quantization layer.

Primary reference:
    Wang, J. (2016). QRDA: Quantum Representation of Digital Audio.
    International Journal of Theoretical Physics, 55, 1622-1641.
    https://doi.org/10.1007/s10773-015-2800-2
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
class QRDAEncodingSpec:
    """Register dimensions and QRDA box metadata for one encoded signal."""

    num_samples: int
    amplitude_bits: int
    time_bits: int
    min_amplitude: int = 0

    @property
    def total_qubits(self) -> int:
        """Return the total number of QRDA data qubits."""
        return self.amplitude_bits + self.time_bits

    @property
    def max_amplitude(self) -> int:
        """Return the maximum unsigned amplitude supported by the register."""
        return (1 << self.amplitude_bits) - 1

    @property
    def box_size(self) -> int:
        """Return the number of time positions in the QRDA 2^l box."""
        return 1 << self.time_bits

    @property
    def padding_count(self) -> int:
        """Return the number of redundant QRDA time positions."""
        return self.box_size - self.num_samples

    @property
    def padding_fraction(self) -> float:
        """Return the fraction of QRDA time positions used as padding."""
        return self.padding_count / self.box_size


def _time_bits_for_length(num_samples: int) -> int:
    """Return the QRDA time-register width defined in the primary paper."""
    if num_samples < 1:
        raise ValueError("num_samples must be positive")
    if num_samples == 1:
        return 1
    return ceil(log2(num_samples))


def _validate_qrda_samples(
    samples: Sequence[int] | Iterable[int],
    amplitude_bits: int | None,
) -> tuple[tuple[int, ...], QRDAEncodingSpec]:
    """Validate unsigned samples and construct their QRDA encoding specification."""
    values = tuple(samples)

    if not values:
        raise ValueError("samples must contain at least one value")

    if any(not isinstance(value, Integral) for value in values):
        raise TypeError("all samples must be integers after quantization")

    if any(int(value) < 0 for value in values):
        raise ValueError("QRDA supports unsigned amplitudes only")

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

    spec = QRDAEncodingSpec(
        num_samples=len(normalized),
        amplitude_bits=selected_bits,
        time_bits=_time_bits_for_length(len(normalized)),
    )
    return normalized, spec


def build_qrda_circuit(
    samples: Sequence[int] | Iterable[int],
    *,
    amplitude_bits: int | None = None,
    add_barriers: bool = True,
) -> tuple[QuantumCircuit, QRDAEncodingSpec]:
    """Build the QRDA preparation circuit for an unsigned quantized audio signal."""
    values, spec = _validate_qrda_samples(samples, amplitude_bits)

    amplitude = QuantumRegister(spec.amplitude_bits, "amplitude")
    time = QuantumRegister(spec.time_bits, "time")
    circuit = QuantumCircuit(amplitude, time, name="qrda_audio")

    circuit.h(time)

    if add_barriers:
        circuit.barrier()

    for time_index, sample in enumerate(values):
        zero_controls = [
            qubit_index
            for qubit_index in range(spec.time_bits)
            if ((time_index >> qubit_index) & 1) == 0
        ]

        for qubit_index in zero_controls:
            circuit.x(time[qubit_index])

        for amplitude_index in range(spec.amplitude_bits):
            if ((sample >> amplitude_index) & 1) == 0:
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


def exact_qrda_probabilities(
    circuit: QuantumCircuit,
    spec: QRDAEncodingSpec,
    *,
    atol: float = 1e-12,
) -> dict[tuple[int, int], float]:
    """Return non-zero QRDA probabilities as (time, amplitude) -> probability."""
    if circuit.num_clbits:
        raise ValueError("exact statevector validation requires an unmeasured circuit")

    if circuit.num_qubits != spec.total_qubits:
        raise ValueError("circuit qubit count does not match the QRDA specification")

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


def simulate_qrda_counts(
    circuit: QuantumCircuit,
    *,
    shots: int = 4096,
    seed_simulator: int = 42,
    optimization_level: int = 1,
    simulator: AerSimulator | None = None,
) -> dict[str, int]:
    """Measure and simulate an unmeasured QRDA circuit with Qiskit Aer."""
    if shots < 1:
        raise ValueError("shots must be a positive integer")

    if circuit.num_clbits:
        raise ValueError("pass the unmeasured QRDA preparation circuit")

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


def decode_qrda_counts(
    counts: Mapping[str, int],
    spec: QRDAEncodingSpec,
) -> dict[int, Counter[int]]:
    """Decode Qiskit counts into amplitude frequencies for every QRDA time index."""
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


def reconstruct_qrda_signal(
    counts: Mapping[str, int],
    spec: QRDAEncodingSpec,
) -> list[int]:
    """Reconstruct only the L effective QRDA samples using modal amplitudes."""
    decoded = decode_qrda_counts(counts, spec)
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


def qrda_resource_metrics(
    circuit: QuantumCircuit,
    *,
    basis_gates: Sequence[str] = ("rz", "sx", "x", "cx"),
    optimization_level: int = 1,
) -> dict[str, object]:
    """Return raw and basis-transpiled QRDA circuit resource metrics."""
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
    "QRDAEncodingSpec",
    "build_qrda_circuit",
    "decode_qrda_counts",
    "exact_qrda_probabilities",
    "qrda_resource_metrics",
    "reconstruct_qrda_signal",
    "simulate_qrda_counts",
]
