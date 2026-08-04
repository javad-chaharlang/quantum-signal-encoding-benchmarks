"""Calibration-derived hardware-noise utilities for basis-encoded audio."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import exp, log1p
from statistics import mean, stdev
from time import perf_counter
from typing import Any

from qiskit import QuantumCircuit, transpile
from qiskit.providers import BackendV2
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from qseb.audio import AudioEncodingSpec, build_basis_encoded_audio_circuit
from qseb.benchmarks.noise_sensitivity import (
    SUMMARY_METRICS,
    evaluate_noisy_counts,
)
from qseb.benchmarks.resource_scaling import generate_profile_samples

CIRCUIT_METRICS = (
    "transpiled_depth",
    "transpiled_size",
    "two_qubit_gate_count",
    "swap_count",
    "calibrated_gate_count",
    "missing_calibration_count",
    "calibration_error_budget",
    "independent_gate_success_proxy",
    "calibrated_duration_seconds",
    "selected_readout_error_mean",
    "selected_readout_error_max",
    "selected_t1_seconds_mean",
    "selected_t2_seconds_mean",
)


@dataclass(frozen=True, slots=True)
class CalibrationNoiseCondition:
    """One ablation of a backend-calibration-derived noise model."""

    name: str
    gate_error: bool
    readout_error: bool
    thermal_relaxation: bool

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("condition name must not be empty")

    @property
    def is_ideal(self) -> bool:
        """Return whether the condition disables every noise component."""

        return not (self.gate_error or self.readout_error or self.thermal_relaxation)


def build_calibration_noise_model(
    backend: BackendV2,
    condition: CalibrationNoiseCondition,
) -> NoiseModel | None:
    """Build an approximate noise model from a BackendV2 calibration snapshot."""

    if condition.is_ideal:
        return None

    return NoiseModel.from_backend(
        backend,
        gate_error=condition.gate_error,
        readout_error=condition.readout_error,
        thermal_relaxation=condition.thermal_relaxation,
    )


def _layout_indices(
    circuit: QuantumCircuit,
    *,
    final: bool,
) -> tuple[int, ...]:
    if circuit.layout is None:
        return tuple(range(circuit.num_qubits))

    if final:
        indices = circuit.layout.final_index_layout(
            filter_ancillas=True,
        )
    else:
        indices = circuit.layout.initial_index_layout(
            filter_ancillas=True,
        )

    return tuple(int(index) for index in indices)


def _target_property(
    backend: BackendV2,
    operation_name: str,
    qargs: tuple[int, ...],
) -> Any | None:
    if operation_name not in backend.target.operation_names:
        return None

    return backend.target[operation_name].get(qargs)


def _optional_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)


def backend_calibration_rows(
    backend: BackendV2,
) -> list[dict[str, object]]:
    """Return qubit and gate calibration records from a backend snapshot."""

    rows: list[dict[str, object]] = []

    for qubit in range(backend.num_qubits):
        try:
            qubit_properties = backend.qubit_properties(qubit)
        except NotImplementedError:
            qubit_properties = None

        measure_properties = _target_property(
            backend,
            "measure",
            (qubit,),
        )

        rows.append(
            {
                "record_type": "qubit",
                "backend_name": backend.name,
                "operation": "qubit",
                "qubits": str(qubit),
                "t1_seconds": _optional_float(getattr(qubit_properties, "t1", None)),
                "t2_seconds": _optional_float(getattr(qubit_properties, "t2", None)),
                "frequency_hz": _optional_float(getattr(qubit_properties, "frequency", None)),
                "instruction_error": _optional_float(getattr(measure_properties, "error", None)),
                "instruction_duration_seconds": _optional_float(
                    getattr(measure_properties, "duration", None)
                ),
            }
        )

    for operation_name in sorted(backend.target.operation_names):
        if operation_name in {"delay", "measure"}:
            continue

        for qargs, properties in backend.target[operation_name].items():
            if qargs is None or properties is None:
                continue

            rows.append(
                {
                    "record_type": "instruction",
                    "backend_name": backend.name,
                    "operation": operation_name,
                    "qubits": "-".join(str(qubit) for qubit in qargs),
                    "t1_seconds": None,
                    "t2_seconds": None,
                    "frequency_hz": None,
                    "instruction_error": _optional_float(getattr(properties, "error", None)),
                    "instruction_duration_seconds": _optional_float(
                        getattr(properties, "duration", None)
                    ),
                }
            )

    return rows


def _selected_qubit_summary(
    backend: BackendV2,
    physical_qubits: Sequence[int],
) -> dict[str, float]:
    readout_errors: list[float] = []
    t1_values: list[float] = []
    t2_values: list[float] = []

    for qubit in physical_qubits:
        measure_properties = _target_property(
            backend,
            "measure",
            (int(qubit),),
        )
        readout_error = getattr(measure_properties, "error", None)
        if readout_error is not None:
            readout_errors.append(float(readout_error))

        try:
            qubit_properties = backend.qubit_properties(int(qubit))
        except NotImplementedError:
            qubit_properties = None

        t1_value = getattr(qubit_properties, "t1", None)
        t2_value = getattr(qubit_properties, "t2", None)

        if t1_value is not None:
            t1_values.append(float(t1_value))
        if t2_value is not None:
            t2_values.append(float(t2_value))

    return {
        "selected_readout_error_mean": (mean(readout_errors) if readout_errors else 0.0),
        "selected_readout_error_max": (max(readout_errors) if readout_errors else 0.0),
        "selected_t1_seconds_mean": mean(t1_values) if t1_values else 0.0,
        "selected_t2_seconds_mean": mean(t2_values) if t2_values else 0.0,
    }


def _circuit_calibration_exposure(
    circuit: QuantumCircuit,
    backend: BackendV2,
) -> dict[str, object]:
    calibrated_gate_count = 0
    missing_calibration_count = 0
    error_budget = 0.0
    duration_seconds = 0.0
    two_qubit_gate_count = 0
    swap_count = 0

    for instruction in circuit.data:
        operation_name = instruction.operation.name

        if operation_name in {"barrier", "measure"}:
            continue

        qargs = tuple(circuit.find_bit(qubit).index for qubit in instruction.qubits)

        if len(qargs) == 2:
            two_qubit_gate_count += 1
        if operation_name == "swap":
            swap_count += 1

        properties = _target_property(
            backend,
            operation_name,
            qargs,
        )
        if properties is None:
            missing_calibration_count += 1
            continue

        calibrated_gate_count += 1
        error = getattr(properties, "error", None)
        duration = getattr(properties, "duration", None)

        if error is not None:
            bounded_error = min(max(float(error), 0.0), 1.0 - 1e-15)
            error_budget += -log1p(-bounded_error)

        if duration is not None:
            duration_seconds += float(duration)

    return {
        "two_qubit_gate_count": two_qubit_gate_count,
        "swap_count": swap_count,
        "calibrated_gate_count": calibrated_gate_count,
        "missing_calibration_count": missing_calibration_count,
        "calibration_error_budget": error_budget,
        "independent_gate_success_proxy": exp(-error_budget),
        "calibrated_duration_seconds": duration_seconds,
    }


def prepare_hardware_noise_circuit(
    backend: BackendV2,
    *,
    num_samples: int,
    amplitude_bits: int,
    data_seed: int,
    optimization_level: int,
    seed_transpiler: int,
) -> tuple[
    QuantumCircuit,
    AudioEncodingSpec,
    list[int],
    dict[str, object],
]:
    """Prepare a measured circuit mapped to one calibration snapshot."""

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
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )

    initial_layout = _layout_indices(compiled, final=False)
    final_layout = _layout_indices(compiled, final=True)
    selected_summary = _selected_qubit_summary(
        backend,
        sorted(set(initial_layout)),
    )
    exposure = _circuit_calibration_exposure(
        compiled,
        backend,
    )

    metadata: dict[str, object] = {
        "seed_transpiler": seed_transpiler,
        "initial_layout": "-".join(str(index) for index in initial_layout),
        "final_layout": "-".join(str(index) for index in final_layout),
        "transpiled_depth": compiled.depth(),
        "transpiled_size": compiled.size(),
        **selected_summary,
        **exposure,
    }

    return compiled, spec, samples, metadata


def simulate_calibration_noise_case(
    *,
    simulator: AerSimulator,
    compiled_circuit: QuantumCircuit,
    spec: AudioEncodingSpec,
    samples: Sequence[int],
    condition: CalibrationNoiseCondition,
    shots: int,
    seed_simulator: int,
) -> dict[str, object]:
    """Run one ideal or calibration-derived noisy simulation."""

    if shots < 1:
        raise ValueError("shots must be a positive integer")

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
        "condition": condition.name,
        "gate_error_enabled": condition.gate_error,
        "readout_error_enabled": condition.readout_error,
        "thermal_relaxation_enabled": condition.thermal_relaxation,
        "seed_simulator": seed_simulator,
        "simulation_seconds": simulation_seconds,
        **metrics,
    }


def run_calibration_hardware_noise(
    backend: BackendV2,
    *,
    sample_counts: Iterable[int],
    conditions: Sequence[CalibrationNoiseCondition],
    layout_seeds: Sequence[int],
    simulator_seeds: Sequence[int],
    amplitude_bits: int = 4,
    shots: int = 2048,
    data_seed: int = 42,
    optimization_level: int = 2,
) -> list[dict[str, object]]:
    """Run calibration-derived noise across layouts and simulator seeds."""

    normalized_samples = tuple(sample_counts)
    normalized_conditions = tuple(conditions)
    normalized_layout_seeds = tuple(layout_seeds)
    normalized_simulator_seeds = tuple(simulator_seeds)

    if not normalized_samples:
        raise ValueError("sample_counts must not be empty")
    if not normalized_conditions:
        raise ValueError("conditions must not be empty")
    if not normalized_layout_seeds:
        raise ValueError("layout_seeds must not be empty")
    if not normalized_simulator_seeds:
        raise ValueError("simulator_seeds must not be empty")

    simulators = {
        condition.name: AerSimulator(
            noise_model=build_calibration_noise_model(
                backend,
                condition,
            )
        )
        for condition in normalized_conditions
    }

    rows: list[dict[str, object]] = []

    for num_samples in normalized_samples:
        for seed_transpiler in normalized_layout_seeds:
            compiled, spec, samples, circuit_metadata = prepare_hardware_noise_circuit(
                backend,
                num_samples=num_samples,
                amplitude_bits=amplitude_bits,
                data_seed=data_seed,
                optimization_level=optimization_level,
                seed_transpiler=seed_transpiler,
            )

            for condition in normalized_conditions:
                for seed_simulator in normalized_simulator_seeds:
                    row = simulate_calibration_noise_case(
                        simulator=simulators[condition.name],
                        compiled_circuit=compiled,
                        spec=spec,
                        samples=samples,
                        condition=condition,
                        shots=shots,
                        seed_simulator=seed_simulator,
                    )
                    row.update(
                        {
                            "backend_name": backend.name,
                            "backend_class": type(backend).__name__,
                            "backend_num_qubits": backend.num_qubits,
                            "num_samples": num_samples,
                            "amplitude_bits": amplitude_bits,
                            "time_bits": spec.time_bits,
                            "logical_qubits": spec.total_qubits,
                            "data_seed": data_seed,
                            "optimization_level": optimization_level,
                            **circuit_metadata,
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
    center = (estimate + z_squared / (2.0 * trials)) / denominator
    margin = (
        z_value
        * (estimate * (1.0 - estimate) / trials + z_squared / (4.0 * trials**2)) ** 0.5
        / denominator
    )

    return max(0.0, center - margin), min(1.0, center + margin)


def aggregate_hardware_noise_rows(
    rows: Iterable[dict[str, object]],
    *,
    by_layout: bool,
) -> list[dict[str, object]]:
    """Aggregate hardware-noise rows globally or by transpiler layout."""

    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        key: tuple[object, ...] = (
            row["num_samples"],
            row["condition"],
        )
        if by_layout:
            key += (
                row["seed_transpiler"],
                row["initial_layout"],
                row["final_layout"],
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
            "backend_name": first["backend_name"],
            "backend_class": first["backend_class"],
            "num_samples": key[0],
            "condition": key[1],
            "runs": runs,
            "shots": first["shots"],
            "amplitude_bits": first["amplitude_bits"],
            "time_bits": first["time_bits"],
            "logical_qubits": first["logical_qubits"],
            "gate_error_enabled": first["gate_error_enabled"],
            "readout_error_enabled": first["readout_error_enabled"],
            "thermal_relaxation_enabled": (first["thermal_relaxation_enabled"]),
            "exact_reconstruction_successes": exact_successes,
            "exact_reconstruction_rate": exact_successes / runs,
            "exact_rate_wilson_95_low": confidence_low,
            "exact_rate_wilson_95_high": confidence_high,
        }

        if by_layout:
            summary.update(
                {
                    "seed_transpiler": key[2],
                    "initial_layout": key[3],
                    "final_layout": key[4],
                }
            )

        for metric in (*SUMMARY_METRICS, *CIRCUIT_METRICS):
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
            str(row["condition"]),
            int(row.get("seed_transpiler", -1)),
        ),
    )
