"""Shot-sensitivity utilities for basis-encoded quantum audio."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import lru_cache
from math import sqrt
from statistics import mean, stdev

import numpy as np

from qseb.audio import (
    build_basis_encoded_audio_circuit,
    decode_measurement_counts,
    reconstruct_from_counts,
    simulate_counts,
)
from qseb.benchmarks.resource_scaling import generate_profile_samples


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _validate_num_samples(num_samples: int) -> None:
    if not isinstance(num_samples, int) or not _is_power_of_two(num_samples):
        raise ValueError("num_samples must be a positive power of two")


def _validate_shots(shots: int) -> None:
    if not isinstance(shots, int) or shots < 1:
        raise ValueError("shots must be a positive integer")


@lru_cache(maxsize=None)
def full_coverage_probability(num_samples: int, shots: int) -> float:
    """Return the exact probability that every time index is observed."""

    _validate_num_samples(num_samples)
    _validate_shots(shots)

    if shots < num_samples:
        return 0.0

    probabilities = [0.0] * (num_samples + 1)
    probabilities[0] = 1.0

    for _ in range(shots):
        updated = [0.0] * (num_samples + 1)

        for observed in range(num_samples + 1):
            probability = probabilities[observed]
            if probability == 0.0:
                continue

            updated[observed] += probability * (observed / num_samples)

            if observed < num_samples:
                updated[observed + 1] += probability * (
                    (num_samples - observed) / num_samples
                )

        probabilities = updated

    return min(1.0, max(0.0, probabilities[num_samples]))


def expected_missing_indices(num_samples: int, shots: int) -> float:
    """Return the expected number of unobserved time indices."""

    _validate_num_samples(num_samples)
    _validate_shots(shots)
    return num_samples * ((num_samples - 1) / num_samples) ** shots


def expected_coverage_fraction(num_samples: int, shots: int) -> float:
    """Return the expected fraction of observed time indices."""

    return 1.0 - (expected_missing_indices(num_samples, shots) / num_samples)


def minimum_shots_for_probability(
    num_samples: int,
    target_probability: float,
    *,
    maximum_shots: int = 1_000_000,
) -> int:
    """Return the minimum shots needed to reach a full-coverage probability."""

    _validate_num_samples(num_samples)

    if not 0.0 < target_probability < 1.0:
        raise ValueError("target_probability must be strictly between zero and one")

    if maximum_shots < 1:
        raise ValueError("maximum_shots must be positive")

    for shots in range(1, maximum_shots + 1):
        if full_coverage_probability(num_samples, shots) >= target_probability:
            return shots

    raise RuntimeError(
        f"target probability {target_probability} was not reached by "
        f"{maximum_shots} shots"
    )


def simulate_ideal_shot_case(
    *,
    num_samples: int,
    shots: int,
    seed: int,
) -> dict[str, object]:
    """Sample the ideal uniform time-index marginal for one experiment run."""

    _validate_num_samples(num_samples)
    _validate_shots(shots)

    generator = np.random.default_rng(seed)
    probabilities = np.full(num_samples, 1.0 / num_samples, dtype=float)
    time_counts = generator.multinomial(shots, probabilities)

    observed_indices = int(np.count_nonzero(time_counts))
    missing_indices = num_samples - observed_indices
    coverage_fraction = observed_indices / num_samples
    empirical_distribution = time_counts / shots
    total_variation_distance = 0.5 * float(
        np.abs(empirical_distribution - probabilities).sum()
    )

    mean_count = shots / num_samples
    count_standard_deviation = float(np.std(time_counts, ddof=0))
    count_coefficient_of_variation = (
        count_standard_deviation / mean_count if mean_count > 0 else 0.0
    )

    return {
        "num_samples": num_samples,
        "time_bits": num_samples.bit_length() - 1,
        "shots": shots,
        "shots_per_sample": shots / num_samples,
        "seed": seed,
        "observed_indices": observed_indices,
        "missing_indices": missing_indices,
        "coverage_fraction": coverage_fraction,
        "exact_reconstruction": missing_indices == 0,
        "minimum_index_count": int(time_counts.min()),
        "maximum_index_count": int(time_counts.max()),
        "count_standard_deviation": count_standard_deviation,
        "count_coefficient_of_variation": count_coefficient_of_variation,
        "time_distribution_tvd": total_variation_distance,
    }


def run_shot_sensitivity(
    *,
    sample_counts: Iterable[int] = (4, 8, 16, 32),
    shot_counts: Iterable[int] = (
        4,
        8,
        16,
        32,
        64,
        128,
        256,
        512,
        1024,
        2048,
        4096,
    ),
    seeds: Sequence[int] = tuple(42 + (10 * index) for index in range(50)),
) -> list[dict[str, object]]:
    """Run the ideal shot-sensitivity Monte Carlo experiment."""

    normalized_samples = tuple(sample_counts)
    normalized_shots = tuple(shot_counts)
    normalized_seeds = tuple(seeds)

    if not normalized_samples:
        raise ValueError("sample_counts must contain at least one value")
    if not normalized_shots:
        raise ValueError("shot_counts must contain at least one value")
    if not normalized_seeds:
        raise ValueError("seeds must contain at least one value")

    for num_samples in normalized_samples:
        _validate_num_samples(num_samples)
    for shots in normalized_shots:
        _validate_shots(shots)

    rows: list[dict[str, object]] = []

    for num_samples in normalized_samples:
        for shots in normalized_shots:
            for seed in normalized_seeds:
                rows.append(
                    simulate_ideal_shot_case(
                        num_samples=num_samples,
                        shots=shots,
                        seed=seed,
                    )
                )

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
        * sqrt(
            (estimate * (1.0 - estimate) / trials)
            + (z_squared / (4.0 * trials**2))
        )
        / denominator
    )

    return max(0.0, center - margin), min(1.0, center + margin)


def aggregate_shot_sensitivity_rows(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Aggregate Monte Carlo rows by signal length and shot count."""

    groups: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        key = (int(row["num_samples"]), int(row["shots"]))
        groups[key].append(row)

    summaries: list[dict[str, object]] = []

    for (num_samples, shots), group in sorted(groups.items()):
        runs = len(group)
        exact_successes = sum(
            1 for row in group if bool(row["exact_reconstruction"])
        )
        empirical_exact_rate = exact_successes / runs
        confidence_low, confidence_high = _wilson_interval(
            exact_successes,
            runs,
        )

        coverage_values = [
            float(row["coverage_fraction"]) for row in group
        ]
        missing_values = [float(row["missing_indices"]) for row in group]
        tvd_values = [
            float(row["time_distribution_tvd"]) for row in group
        ]
        coefficient_values = [
            float(row["count_coefficient_of_variation"]) for row in group
        ]

        theoretical_full_coverage = full_coverage_probability(
            num_samples,
            shots,
        )
        theoretical_expected_missing = expected_missing_indices(
            num_samples,
            shots,
        )
        theoretical_expected_coverage = expected_coverage_fraction(
            num_samples,
            shots,
        )

        summaries.append(
            {
                "num_samples": num_samples,
                "time_bits": num_samples.bit_length() - 1,
                "shots": shots,
                "shots_per_sample": shots / num_samples,
                "runs": runs,
                "exact_reconstruction_successes": exact_successes,
                "empirical_exact_reconstruction_rate": empirical_exact_rate,
                "exact_rate_wilson_95_low": confidence_low,
                "exact_rate_wilson_95_high": confidence_high,
                "theoretical_full_coverage_probability": theoretical_full_coverage,
                "exact_rate_absolute_error": abs(
                    empirical_exact_rate - theoretical_full_coverage
                ),
                "coverage_fraction_mean": mean(coverage_values),
                "coverage_fraction_std": (
                    stdev(coverage_values) if runs > 1 else 0.0
                ),
                "theoretical_expected_coverage_fraction": (
                    theoretical_expected_coverage
                ),
                "coverage_mean_absolute_error": abs(
                    mean(coverage_values) - theoretical_expected_coverage
                ),
                "missing_indices_mean": mean(missing_values),
                "missing_indices_std": (
                    stdev(missing_values) if runs > 1 else 0.0
                ),
                "theoretical_expected_missing_indices": (
                    theoretical_expected_missing
                ),
                "time_distribution_tvd_mean": mean(tvd_values),
                "time_distribution_tvd_std": (
                    stdev(tvd_values) if runs > 1 else 0.0
                ),
                "count_coefficient_of_variation_mean": mean(coefficient_values),
                "count_coefficient_of_variation_std": (
                    stdev(coefficient_values) if runs > 1 else 0.0
                ),
            }
        )

    return summaries


def validate_qiskit_shot_case(
    *,
    num_samples: int,
    amplitude_bits: int,
    shots: int,
    seed: int = 42,
    optimization_level: int = 1,
) -> dict[str, object]:
    """Run one actual Qiskit Aer encode-measure-decode validation case."""

    _validate_num_samples(num_samples)
    _validate_shots(shots)

    samples = generate_profile_samples(
        num_samples,
        amplitude_bits,
        profile="random",
        seed=seed,
    )
    circuit, spec = build_basis_encoded_audio_circuit(
        samples,
        amplitude_bits=amplitude_bits,
    )
    counts = simulate_counts(
        circuit,
        shots=shots,
        seed_simulator=seed,
        optimization_level=optimization_level,
    )
    decoded = decode_measurement_counts(counts, spec)
    observed_indices = len(decoded)
    missing_indices = num_samples - observed_indices

    observed_amplitudes_correct = all(
        set(amplitude_counts) == {samples[time_index]}
        for time_index, amplitude_counts in decoded.items()
    )

    reconstructed: list[int] | None
    exact_reconstruction: bool

    if missing_indices == 0:
        reconstructed = reconstruct_from_counts(counts, spec)
        exact_reconstruction = reconstructed == samples
    else:
        reconstructed = None
        exact_reconstruction = False

    return {
        "num_samples": num_samples,
        "amplitude_bits": amplitude_bits,
        "time_bits": spec.time_bits,
        "total_qubits": spec.total_qubits,
        "shots": shots,
        "seed": seed,
        "observed_indices": observed_indices,
        "missing_indices": missing_indices,
        "coverage_fraction": observed_indices / num_samples,
        "observed_amplitudes_correct": observed_amplitudes_correct,
        "exact_reconstruction": exact_reconstruction,
        "original_samples": samples,
        "reconstructed_samples": reconstructed,
    }
