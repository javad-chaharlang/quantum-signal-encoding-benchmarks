"""Tests for controlled resource-scaling benchmark utilities."""

from __future__ import annotations

import pytest

from qseb.benchmarks import (
    aggregate_resource_rows,
    benchmark_resource_case,
    generate_deterministic_samples,
    generate_profile_samples,
    run_amplitude_resolution_scaling,
    run_signal_length_scaling,
)


def test_random_profile_is_reproducible_and_bounded() -> None:
    first = generate_deterministic_samples(8, 4, seed=42)
    second = generate_profile_samples(8, 4, profile="random", seed=42)

    assert first == second
    assert len(first) == 8
    assert all(0 <= value <= 15 for value in first)


def test_sparse_profile_has_one_set_bit_per_sample() -> None:
    samples = generate_profile_samples(8, 4, profile="sparse")

    assert sum(value.bit_count() for value in samples) == 8
    assert all(value > 0 for value in samples)


def test_dense_profile_sets_every_amplitude_bit() -> None:
    samples = generate_profile_samples(8, 4, profile="dense")

    assert samples == [15] * 8
    assert sum(value.bit_count() for value in samples) == 32


@pytest.mark.parametrize("num_samples", [0, 3, 6])
def test_profiles_reject_invalid_lengths(num_samples: int) -> None:
    with pytest.raises(ValueError, match="power of two"):
        generate_profile_samples(num_samples, 4)


def test_profiles_reject_unknown_profile() -> None:
    with pytest.raises(ValueError, match="profile"):
        generate_profile_samples(8, 4, profile="unknown")


def test_small_resource_case_reports_expected_dimensions() -> None:
    row = benchmark_resource_case(
        num_samples=2,
        amplitude_bits=2,
        profile="sparse",
        seed=42,
        optimization_level=0,
        timing_repeats=1,
    )

    assert row["profile"] == "sparse"
    assert row["time_bits"] == 1
    assert row["total_qubits"] == 3
    assert row["state_space_dimension"] == 8
    assert row["sample_hamming_weight"] == 2
    assert int(row["raw_size"]) > 0
    assert int(row["transpiled_size"]) > 0
    assert float(row["transpile_seconds"]) >= 0.0


def test_scaling_study_counts_profiles_and_random_seeds() -> None:
    rows = run_signal_length_scaling(
        (2,),
        amplitude_bits=2,
        profiles=("sparse", "random", "dense"),
        random_seeds=(42, 52),
        optimization_level=0,
        timing_repeats=1,
    )

    assert len(rows) == 4
    assert [row["profile"] for row in rows].count("random") == 2


def test_amplitude_study_preserves_requested_widths() -> None:
    rows = run_amplitude_resolution_scaling(
        (2, 3),
        num_samples=2,
        profiles=("sparse",),
        random_seeds=(42,),
        optimization_level=0,
        timing_repeats=1,
    )

    assert [row["amplitude_bits"] for row in rows] == [2, 3]


def test_aggregation_reports_mean_and_standard_deviation() -> None:
    rows = [
        {
            "study": "signal_length",
            "profile": "random",
            "num_samples": 2,
            "amplitude_bits": 2,
            "time_bits": 1,
            "total_qubits": 3,
            "state_space_dimension": 8,
            "sample_hamming_weight": 2.0,
            "sample_bit_density": 0.5,
            "build_seconds": 0.1,
            "transpile_seconds": 0.2,
            "raw_depth": 4.0,
            "raw_size": 5.0,
            "transpiled_depth": 8.0,
            "transpiled_size": 10.0,
            "transpiled_cx_count": 4.0,
            "transpiled_single_qubit_count": 6.0,
            "depth_overhead_ratio": 2.0,
            "size_overhead_ratio": 2.0,
        },
        {
            "study": "signal_length",
            "profile": "random",
            "num_samples": 2,
            "amplitude_bits": 2,
            "time_bits": 1,
            "total_qubits": 3,
            "state_space_dimension": 8,
            "sample_hamming_weight": 4.0,
            "sample_bit_density": 1.0,
            "build_seconds": 0.2,
            "transpile_seconds": 0.4,
            "raw_depth": 6.0,
            "raw_size": 7.0,
            "transpiled_depth": 12.0,
            "transpiled_size": 14.0,
            "transpiled_cx_count": 8.0,
            "transpiled_single_qubit_count": 10.0,
            "depth_overhead_ratio": 2.0,
            "size_overhead_ratio": 2.0,
        },
    ]

    summary = aggregate_resource_rows(rows)[0]

    assert summary["runs"] == 2
    assert summary["sample_hamming_weight_mean"] == 3.0
    assert summary["transpiled_depth_mean"] == 10.0
    assert float(summary["transpiled_depth_std"]) > 0.0
