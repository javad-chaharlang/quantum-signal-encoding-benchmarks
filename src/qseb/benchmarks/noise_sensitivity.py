"""Controlled noise-sensitivity utilities for basis-encoded quantum audio."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import mean, stdev
from time import perf_counter

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

from qseb.audio import (
    AudioEncodingSpec,
    build_basis_encoded_audio_circuit,
    decode_measurement_counts,
)
from qseb.benchmarks.resource_scaling import generate_profile_samples

DEFAULT_NOISE_BASIS_GATES = ("rz", "sx", "x", "cx")

SUMMARY_METRICS = (
    "coverage_fraction",
    "modal_amplitude_accuracy",
    "normalized_modal_mae",
    "correct_basis_shot_fraction",
    "amplitude_bit_error_rate",
    "joint_distribution_tvd",
    "time_distribution_tvd",
    "simulation_seconds",
)


@dataclass(frozen=True, slots=True)
class NoiseCondition:
    """One synthetic noise configuration."""

    family: str
    severity: str
    severity_index: int
    single_qubit_error: float = 0.0
    two_qubit_error: float = 0.0
    readout_error: float = 0.0

    def __post_init__(self) -> None:
        if not self.family:
            raise ValueError("family must not be empty")

        if not self.severity:
            raise ValueError("severity must not be empty")

        if not isinstance(self.severity_index, int) or self.severity_index < 0:
            raise ValueError("severity_index must be a non-negative integer")

        probabilities = (
            self.single_qubit_error,
            self.two_qubit_error,
            self.readout_error,
        )
        if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
            raise ValueError("noise probabilities must be between zero and one")

    @property
    def is_ideal(self) -> bool:
        """Return whether every configured error probability is zero."""

        return (
            self.single_qubit_error == 0.0
            and self.two_qubit_error == 0.0
            and self.readout_error == 0.0
        )


def _validate_samples(samples: Sequence[int], spec: AudioEncodingSpec) -> None:
    if len(samples) != spec.num_samples:
        raise ValueError("sample count does not match the encoding specification")

    if any(not 0 <= sample <= spec.max_amplitude for sample in samples):
        raise ValueError("sample value is outside the amplitude-register range")


def build_noise_model(condition: NoiseCondition) -> NoiseModel | None:
    """Build an Aer noise model for one controlled synthetic condition."""

    if condition.is_ideal:
        return None

    noise_model = NoiseModel(basis_gates=list(DEFAULT_NOISE_BASIS_GATES))

    if condition.single_qubit_error > 0.0:
        one_qubit_error = depolarizing_error(
            condition.single_qubit_error,
            1,
        )
        noise_model.add_all_qubit_quantum_error(
            one_qubit_error,
            ["sx", "x"],
        )

    if condition.two_qubit_error > 0.0:
        two_qubit_error = depolarizing_error(
            condition.two_qubit_error,
            2,
        )
        noise_model.add_all_qubit_quantum_error(
            two_qubit_error,
            ["cx"],
        )

    if condition.readout_error > 0.0:
        probability = condition.readout_error
        readout_matrix = [
            [1.0 - probability, probability],
            [probability, 1.0 - probability],
        ]
        noise_model.add_all_qubit_readout_error(ReadoutError(readout_matrix))

    return noise_model


def prepare_noise_benchmark_circuit(
    *,
    num_samples: int,
    amplitude_bits: int,
    data_seed: int = 42,
    optimization_level: int = 1,
    seed_transpiler: int = 42,
) -> tuple[QuantumCircuit, AudioEncodingSpec, list[int]]:
    """Prepare and transpile one reusable measured benchmark circuit."""

    samples = generate_profile_samples(
        num_samples,
        amplitude_bits,
        profile="random",
        seed=data_seed,
    )
    circuit, spec = build_basis_encoded_audio_circuit(
        samples,
        amplitude_bits=amplitude_bits,
        add_barriers=False,
    )
    measured = circuit.measure_all(inplace=False)
    compiled = transpile(
        measured,
        basis_gates=list(DEFAULT_NOISE_BASIS_GATES),
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )

    return compiled, spec, samples


def _modal_amplitude(frequencies: Mapping[int, int]) -> int:
    return min(
        frequencies,
        key=lambda amplitude: (-frequencies[amplitude], amplitude),
    )


def evaluate_noisy_counts(
    counts: Mapping[str, int],
    spec: AudioEncodingSpec,
    samples: Sequence[int],
) -> dict[str, object]:
    """Evaluate reconstruction and distribution metrics from noisy counts."""

    _validate_samples(samples, spec)

    total_shots = sum(int(count) for count in counts.values())
    if total_shots < 1:
        raise ValueError("counts must contain at least one measurement")

    decoded = decode_measurement_counts(counts, spec)
    ideal_probability = 1.0 / spec.num_samples

    correct_basis_shots = 0
    amplitude_bit_errors = 0
    modal_correct = 0
    normalized_modal_errors: list[float] = []
    time_counts = [0] * spec.num_samples

    for time_index in range(spec.num_samples):
        frequencies = decoded.get(time_index)
        true_amplitude = int(samples[time_index])

        if not frequencies:
            normalized_modal_errors.append(1.0)
            continue

        time_counts[time_index] = sum(frequencies.values())
        correct_basis_shots += frequencies.get(true_amplitude, 0)

        for measured_amplitude, frequency in frequencies.items():
            bit_errors = (measured_amplitude ^ true_amplitude).bit_count()
            amplitude_bit_errors += bit_errors * frequency

        modal_amplitude = _modal_amplitude(frequencies)
        if modal_amplitude == true_amplitude:
            modal_correct += 1

        if spec.max_amplitude:
            normalized_error = abs(modal_amplitude - true_amplitude) / spec.max_amplitude
        else:
            normalized_error = 0.0
        normalized_modal_errors.append(normalized_error)

    observed_indices = sum(count > 0 for count in time_counts)
    coverage_fraction = observed_indices / spec.num_samples
    modal_amplitude_accuracy = modal_correct / spec.num_samples

    empirical_joint: dict[tuple[int, int], float] = {}
    for time_index, frequencies in decoded.items():
        for amplitude, frequency in frequencies.items():
            empirical_joint[(time_index, amplitude)] = frequency / total_shots

    joint_states = set(empirical_joint)
    joint_states.update(
        (time_index, int(samples[time_index])) for time_index in range(spec.num_samples)
    )
    joint_distribution_tvd = 0.5 * sum(
        abs(
            empirical_joint.get(state, 0.0)
            - (ideal_probability if state[1] == int(samples[state[0]]) else 0.0)
        )
        for state in joint_states
    )

    time_distribution_tvd = 0.5 * sum(
        abs((count / total_shots) - ideal_probability) for count in time_counts
    )

    return {
        "shots": total_shots,
        "observed_indices": observed_indices,
        "coverage_fraction": coverage_fraction,
        "modal_correct_indices": modal_correct,
        "modal_amplitude_accuracy": modal_amplitude_accuracy,
        "normalized_modal_mae": mean(normalized_modal_errors),
        "correct_basis_shot_fraction": correct_basis_shots / total_shots,
        "amplitude_bit_error_rate": (amplitude_bit_errors / (total_shots * spec.amplitude_bits)),
        "joint_distribution_tvd": joint_distribution_tvd,
        "time_distribution_tvd": time_distribution_tvd,
        "exact_reconstruction": modal_correct == spec.num_samples,
    }


def simulate_noise_case(
    *,
    compiled_circuit: QuantumCircuit,
    spec: AudioEncodingSpec,
    samples: Sequence[int],
    condition: NoiseCondition,
    shots: int,
    seed_simulator: int,
) -> dict[str, object]:
    """Simulate and evaluate one noisy benchmark run."""

    if shots < 1:
        raise ValueError("shots must be a positive integer")

    noise_model = build_noise_model(condition)
    simulator = AerSimulator(noise_model=noise_model)

    start = perf_counter()
    result = simulator.run(
        compiled_circuit,
        shots=shots,
        seed_simulator=seed_simulator,
    ).result()
    simulation_seconds = perf_counter() - start

    metrics = evaluate_noisy_counts(
        dict(result.get_counts()),
        spec,
        samples,
    )

    return {
        "family": condition.family,
        "severity": condition.severity,
        "severity_index": condition.severity_index,
        "single_qubit_error": condition.single_qubit_error,
        "two_qubit_error": condition.two_qubit_error,
        "readout_error": condition.readout_error,
        "seed_simulator": seed_simulator,
        "simulation_seconds": simulation_seconds,
        **metrics,
    }


def run_noise_sensitivity(
    *,
    sample_counts: Iterable[int],
    conditions: Sequence[NoiseCondition],
    seeds: Sequence[int],
    amplitude_bits: int = 4,
    shots: int = 1024,
    data_seed: int = 42,
    optimization_level: int = 1,
    seed_transpiler: int = 42,
) -> list[dict[str, object]]:
    """Run the complete controlled noise-sensitivity grid."""

    normalized_samples = tuple(sample_counts)
    normalized_conditions = tuple(conditions)
    normalized_seeds = tuple(seeds)

    if not normalized_samples:
        raise ValueError("sample_counts must contain at least one value")

    if not normalized_conditions:
        raise ValueError("conditions must contain at least one value")

    if not normalized_seeds:
        raise ValueError("seeds must contain at least one value")

    rows: list[dict[str, object]] = []

    for num_samples in normalized_samples:
        compiled, spec, samples = prepare_noise_benchmark_circuit(
            num_samples=num_samples,
            amplitude_bits=amplitude_bits,
            data_seed=data_seed,
            optimization_level=optimization_level,
            seed_transpiler=seed_transpiler,
        )
        operation_counts = dict(compiled.count_ops())

        for condition in normalized_conditions:
            for seed in normalized_seeds:
                row = simulate_noise_case(
                    compiled_circuit=compiled,
                    spec=spec,
                    samples=samples,
                    condition=condition,
                    shots=shots,
                    seed_simulator=seed,
                )
                row.update(
                    {
                        "num_samples": num_samples,
                        "amplitude_bits": amplitude_bits,
                        "time_bits": spec.time_bits,
                        "total_qubits": spec.total_qubits,
                        "data_seed": data_seed,
                        "seed_transpiler": seed_transpiler,
                        "optimization_level": optimization_level,
                        "transpiled_depth": compiled.depth(),
                        "transpiled_size": compiled.size(),
                        "transpiled_cx_count": int(operation_counts.get("cx", 0)),
                    }
                )
                rows.append(row)

    return rows


def _wilson_interval(
    successes: int,
    trials: int,
    *,
    z_value: float = 1.959963984540054,
) -> tuple[float, float]:
    if trials < 1:
        raise ValueError("trials must be positive")

    estimate = successes / trials
    z_squared = z_value**2
    denominator = 1.0 + (z_squared / trials)
    center = (estimate + (z_squared / (2.0 * trials))) / denominator
    margin = (
        z_value
        * ((estimate * (1.0 - estimate) / trials + z_squared / (4.0 * trials**2)) ** 0.5)
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def aggregate_noise_sensitivity_rows(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Aggregate repeated noisy simulations by condition and signal length."""

    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        key = (
            row["num_samples"],
            row["family"],
            row["severity"],
            row["severity_index"],
            row["single_qubit_error"],
            row["two_qubit_error"],
            row["readout_error"],
        )
        groups[key].append(row)

    summaries: list[dict[str, object]] = []

    for key, group in groups.items():
        first = group[0]
        runs = len(group)
        exact_successes = sum(1 for row in group if bool(row["exact_reconstruction"]))
        confidence_low, confidence_high = _wilson_interval(
            exact_successes,
            runs,
        )

        summary: dict[str, object] = {
            "num_samples": key[0],
            "family": key[1],
            "severity": key[2],
            "severity_index": key[3],
            "single_qubit_error": key[4],
            "two_qubit_error": key[5],
            "readout_error": key[6],
            "amplitude_bits": first["amplitude_bits"],
            "time_bits": first["time_bits"],
            "total_qubits": first["total_qubits"],
            "shots": first["shots"],
            "runs": runs,
            "transpiled_depth": first["transpiled_depth"],
            "transpiled_size": first["transpiled_size"],
            "transpiled_cx_count": first["transpiled_cx_count"],
            "exact_reconstruction_successes": exact_successes,
            "exact_reconstruction_rate": exact_successes / runs,
            "exact_rate_wilson_95_low": confidence_low,
            "exact_rate_wilson_95_high": confidence_high,
        }

        for metric in SUMMARY_METRICS:
            values = [float(row[metric]) for row in group]
            summary[f"{metric}_mean"] = mean(values)
            summary[f"{metric}_std"] = stdev(values) if len(values) > 1 else 0.0
            summary[f"{metric}_min"] = min(values)
            summary[f"{metric}_max"] = max(values)

        summaries.append(summary)

    return sorted(
        summaries,
        key=lambda row: (
            int(row["num_samples"]),
            int(row["severity_index"]),
            str(row["family"]),
        ),
    )
