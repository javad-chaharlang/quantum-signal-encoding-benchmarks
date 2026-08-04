"""Controlled resource-scaling benchmarks for quantum signal encodings."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from random import Random
from statistics import mean, median, stdev
from time import perf_counter

from qiskit import transpile

from qseb.audio import build_basis_encoded_audio_circuit

DEFAULT_BASIS_GATES = ("rz", "sx", "x", "cx")
VALID_PROFILES = ("sparse", "random", "dense")

SUMMARY_METRICS = (
    "sample_hamming_weight",
    "sample_bit_density",
    "build_seconds",
    "transpile_seconds",
    "raw_depth",
    "raw_size",
    "transpiled_depth",
    "transpiled_size",
    "transpiled_cx_count",
    "transpiled_single_qubit_count",
    "depth_overhead_ratio",
    "size_overhead_ratio",
)


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _validate_case_dimensions(num_samples: int, amplitude_bits: int) -> None:
    if not isinstance(num_samples, int) or not _is_power_of_two(num_samples):
        raise ValueError("num_samples must be a positive power of two")

    if not isinstance(amplitude_bits, int) or amplitude_bits < 1:
        raise ValueError("amplitude_bits must be a positive integer")


def generate_profile_samples(
    num_samples: int,
    amplitude_bits: int,
    *,
    profile: str = "random",
    seed: int = 42,
) -> list[int]:
    """Generate one reproducible signal profile for a benchmark case.

    Profiles:
        sparse: exactly one set amplitude bit per sample.
        random: uniformly sampled unsigned amplitudes using a deterministic seed.
        dense: every amplitude bit is set for every sample.
    """

    _validate_case_dimensions(num_samples, amplitude_bits)

    if profile not in VALID_PROFILES:
        raise ValueError(f"profile must be one of {VALID_PROFILES}")

    maximum = (1 << amplitude_bits) - 1

    if profile == "sparse":
        return [1 << (index % amplitude_bits) for index in range(num_samples)]

    if profile == "dense":
        return [maximum] * num_samples

    case_seed = seed + (num_samples * 1009) + (amplitude_bits * 9173)
    generator = Random(case_seed)
    samples = [generator.randrange(maximum + 1) for _ in range(num_samples)]

    if all(value == 0 for value in samples):
        samples[0] = maximum

    return samples


def generate_deterministic_samples(
    num_samples: int,
    amplitude_bits: int,
    *,
    seed: int = 42,
) -> list[int]:
    """Backward-compatible helper returning the deterministic random profile."""

    return generate_profile_samples(
        num_samples,
        amplitude_bits,
        profile="random",
        seed=seed,
    )


def benchmark_resource_case(
    *,
    num_samples: int,
    amplitude_bits: int,
    profile: str = "random",
    seed: int = 42,
    optimization_level: int = 1,
    basis_gates: Sequence[str] = DEFAULT_BASIS_GATES,
    seed_transpiler: int = 42,
    timing_repeats: int = 3,
) -> dict[str, object]:
    """Benchmark circuit construction and transpiled resource requirements."""

    _validate_case_dimensions(num_samples, amplitude_bits)

    if not isinstance(timing_repeats, int) or timing_repeats < 1:
        raise ValueError("timing_repeats must be a positive integer")

    samples = generate_profile_samples(
        num_samples,
        amplitude_bits,
        profile=profile,
        seed=seed,
    )

    build_start = perf_counter()
    circuit, spec = build_basis_encoded_audio_circuit(
        samples,
        amplitude_bits=amplitude_bits,
        add_barriers=False,
    )
    build_seconds = perf_counter() - build_start

    transpile_durations: list[float] = []
    compiled = None

    for _ in range(timing_repeats):
        transpile_start = perf_counter()
        compiled = transpile(
            circuit,
            basis_gates=list(basis_gates),
            optimization_level=optimization_level,
            seed_transpiler=seed_transpiler,
        )
        transpile_durations.append(perf_counter() - transpile_start)

    if compiled is None:
        raise RuntimeError("transpilation did not produce a circuit")

    raw_operations = dict(circuit.count_ops())
    transpiled_operations = dict(compiled.count_ops())
    transpiled_single_qubit_count = sum(
        int(transpiled_operations.get(gate, 0)) for gate in ("rz", "sx", "x")
    )
    sample_hamming_weight = sum(value.bit_count() for value in samples)
    available_amplitude_bits = num_samples * amplitude_bits

    raw_depth = int(circuit.depth())
    raw_size = int(circuit.size())
    transpiled_depth = int(compiled.depth())
    transpiled_size = int(compiled.size())

    return {
        "profile": profile,
        "num_samples": num_samples,
        "amplitude_bits": amplitude_bits,
        "time_bits": spec.time_bits,
        "total_qubits": spec.total_qubits,
        "state_space_dimension": 1 << spec.total_qubits,
        "seed": seed,
        "seed_transpiler": seed_transpiler,
        "optimization_level": optimization_level,
        "basis_gates": list(basis_gates),
        "timing_repeats": timing_repeats,
        "sample_min": min(samples),
        "sample_max": max(samples),
        "sample_mean": sum(samples) / len(samples),
        "sample_hamming_weight": sample_hamming_weight,
        "sample_bit_density": sample_hamming_weight / available_amplitude_bits,
        "build_seconds": build_seconds,
        "transpile_seconds": median(transpile_durations),
        "transpile_seconds_min": min(transpile_durations),
        "transpile_seconds_max": max(transpile_durations),
        "raw_depth": raw_depth,
        "raw_size": raw_size,
        "raw_operations": raw_operations,
        "transpiled_depth": transpiled_depth,
        "transpiled_size": transpiled_size,
        "transpiled_operations": transpiled_operations,
        "transpiled_cx_count": int(transpiled_operations.get("cx", 0)),
        "transpiled_single_qubit_count": transpiled_single_qubit_count,
        "depth_overhead_ratio": transpiled_depth / raw_depth,
        "size_overhead_ratio": transpiled_size / raw_size,
    }


def _validate_profiles(profiles: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(profiles)

    if not normalized:
        raise ValueError("profiles must contain at least one value")

    invalid = [profile for profile in normalized if profile not in VALID_PROFILES]
    if invalid:
        raise ValueError(f"invalid profiles: {invalid}; expected values from {VALID_PROFILES}")

    return normalized


def _seeds_for_profile(profile: str, random_seeds: Sequence[int]) -> tuple[int, ...]:
    if profile == "random":
        if not random_seeds:
            raise ValueError("random_seeds must not be empty when using the random profile")
        return tuple(random_seeds)

    return (random_seeds[0] if random_seeds else 42,)


def run_signal_length_scaling(
    sample_counts: Iterable[int] = (2, 4, 8, 16, 32),
    *,
    amplitude_bits: int = 4,
    profiles: Iterable[str] = VALID_PROFILES,
    random_seeds: Sequence[int] = (42, 52, 62, 72, 82),
    optimization_level: int = 1,
    basis_gates: Sequence[str] = DEFAULT_BASIS_GATES,
    seed_transpiler: int = 42,
    timing_repeats: int = 3,
) -> list[dict[str, object]]:
    """Measure resource growth as the number of signal samples increases."""

    normalized_counts = tuple(sample_counts)
    normalized_profiles = _validate_profiles(profiles)

    if not normalized_counts:
        raise ValueError("sample_counts must contain at least one value")

    if any(not _is_power_of_two(value) for value in normalized_counts):
        raise ValueError("every sample count must be a positive power of two")

    rows: list[dict[str, object]] = []

    for num_samples in normalized_counts:
        for profile in normalized_profiles:
            for seed in _seeds_for_profile(profile, random_seeds):
                row = benchmark_resource_case(
                    num_samples=num_samples,
                    amplitude_bits=amplitude_bits,
                    profile=profile,
                    seed=seed,
                    optimization_level=optimization_level,
                    basis_gates=basis_gates,
                    seed_transpiler=seed_transpiler,
                    timing_repeats=timing_repeats,
                )
                row["study"] = "signal_length"
                rows.append(row)

    return rows


def run_amplitude_resolution_scaling(
    amplitude_widths: Iterable[int] = (2, 3, 4, 5, 6, 7, 8),
    *,
    num_samples: int = 8,
    profiles: Iterable[str] = VALID_PROFILES,
    random_seeds: Sequence[int] = (42, 52, 62, 72, 82),
    optimization_level: int = 1,
    basis_gates: Sequence[str] = DEFAULT_BASIS_GATES,
    seed_transpiler: int = 42,
    timing_repeats: int = 3,
) -> list[dict[str, object]]:
    """Measure resource growth as the amplitude-register width increases."""

    normalized_widths = tuple(amplitude_widths)
    normalized_profiles = _validate_profiles(profiles)

    if not normalized_widths:
        raise ValueError("amplitude_widths must contain at least one value")

    if any(not isinstance(value, int) or value < 1 for value in normalized_widths):
        raise ValueError("every amplitude width must be a positive integer")

    if not _is_power_of_two(num_samples):
        raise ValueError("num_samples must be a positive power of two")

    rows: list[dict[str, object]] = []

    for amplitude_bits in normalized_widths:
        for profile in normalized_profiles:
            for seed in _seeds_for_profile(profile, random_seeds):
                row = benchmark_resource_case(
                    num_samples=num_samples,
                    amplitude_bits=amplitude_bits,
                    profile=profile,
                    seed=seed,
                    optimization_level=optimization_level,
                    basis_gates=basis_gates,
                    seed_transpiler=seed_transpiler,
                    timing_repeats=timing_repeats,
                )
                row["study"] = "amplitude_resolution"
                rows.append(row)

    return rows


def aggregate_resource_rows(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Aggregate repeated runs by study, profile, and scaling dimensions."""

    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        key = (
            row["study"],
            row["profile"],
            row["num_samples"],
            row["amplitude_bits"],
        )
        groups[key].append(row)

    summaries: list[dict[str, object]] = []

    for key, group in groups.items():
        first = group[0]
        summary: dict[str, object] = {
            "study": key[0],
            "profile": key[1],
            "num_samples": key[2],
            "amplitude_bits": key[3],
            "time_bits": first["time_bits"],
            "total_qubits": first["total_qubits"],
            "state_space_dimension": first["state_space_dimension"],
            "runs": len(group),
        }

        for metric in SUMMARY_METRICS:
            values = [float(row[metric]) for row in group]
            summary[f"{metric}_mean"] = mean(values)
            summary[f"{metric}_std"] = stdev(values) if len(values) > 1 else 0.0
            summary[f"{metric}_min"] = min(values)
            summary[f"{metric}_max"] = max(values)

        summaries.append(summary)

    return summaries
