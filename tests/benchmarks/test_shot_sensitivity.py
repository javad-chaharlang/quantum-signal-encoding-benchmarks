"""Tests for the shot-sensitivity benchmark."""

from __future__ import annotations

import pytest

from qseb.benchmarks import (
    aggregate_shot_sensitivity_rows,
    expected_coverage_fraction,
    expected_missing_indices,
    full_coverage_probability,
    minimum_shots_for_probability,
    run_shot_sensitivity,
    simulate_ideal_shot_case,
)


def test_full_coverage_probability_for_two_indices_and_two_shots() -> None:
    assert full_coverage_probability(2, 2) == pytest.approx(0.5)


def test_full_coverage_is_impossible_when_shots_are_too_few() -> None:
    assert full_coverage_probability(8, 7) == 0.0


def test_expected_missing_and_coverage_are_complements() -> None:
    missing = expected_missing_indices(8, 16)
    coverage = expected_coverage_fraction(8, 16)

    assert coverage == pytest.approx(1.0 - (missing / 8))


def test_minimum_shots_reaches_requested_probability() -> None:
    shots = minimum_shots_for_probability(4, 0.95)

    assert full_coverage_probability(4, shots) >= 0.95
    assert full_coverage_probability(4, shots - 1) < 0.95


def test_ideal_shot_case_is_reproducible() -> None:
    first = simulate_ideal_shot_case(
        num_samples=8,
        shots=32,
        seed=42,
    )
    second = simulate_ideal_shot_case(
        num_samples=8,
        shots=32,
        seed=42,
    )

    assert first == second
    assert first["exact_reconstruction"] == (
        first["missing_indices"] == 0
    )


def test_shot_case_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="power of two"):
        simulate_ideal_shot_case(
            num_samples=6,
            shots=32,
            seed=42,
        )

    with pytest.raises(ValueError, match="positive integer"):
        simulate_ideal_shot_case(
            num_samples=8,
            shots=0,
            seed=42,
        )


def test_run_and_aggregation_shapes() -> None:
    raw_rows = run_shot_sensitivity(
        sample_counts=(4, 8),
        shot_counts=(8, 16),
        seeds=(42, 52, 62),
    )
    summary_rows = aggregate_shot_sensitivity_rows(raw_rows)

    assert len(raw_rows) == 12
    assert len(summary_rows) == 4
    assert all(row["runs"] == 3 for row in summary_rows)


def test_empirical_summary_contains_theoretical_reference() -> None:
    raw_rows = run_shot_sensitivity(
        sample_counts=(4,),
        shot_counts=(16,),
        seeds=(42, 52, 62, 72),
    )
    summary = aggregate_shot_sensitivity_rows(raw_rows)[0]

    assert 0.0 <= summary["empirical_exact_reconstruction_rate"] <= 1.0
    assert 0.0 <= summary["theoretical_full_coverage_probability"] <= 1.0
    assert summary["theoretical_expected_missing_indices"] >= 0.0
