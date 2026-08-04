"""Tests for controlled noise-sensitivity utilities."""

from __future__ import annotations

import pytest

from qseb.audio import AudioEncodingSpec
from qseb.benchmarks import (
    NoiseCondition,
    aggregate_noise_sensitivity_rows,
    build_noise_model,
    evaluate_noisy_counts,
    prepare_noise_benchmark_circuit,
    simulate_noise_case,
)


def test_noise_condition_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        NoiseCondition(
            family="gate",
            severity="invalid",
            severity_index=1,
            single_qubit_error=1.1,
        )


def test_ideal_condition_has_no_noise_model() -> None:
    condition = NoiseCondition(
        family="ideal",
        severity="ideal",
        severity_index=0,
    )

    assert condition.is_ideal
    assert build_noise_model(condition) is None


def test_readout_condition_builds_nonideal_model() -> None:
    condition = NoiseCondition(
        family="readout",
        severity="test",
        severity_index=1,
        readout_error=0.01,
    )
    model = build_noise_model(condition)

    assert model is not None
    assert not model.is_ideal()


def test_evaluate_ideal_counts_reports_exact_reconstruction() -> None:
    spec = AudioEncodingSpec(
        num_samples=2,
        amplitude_bits=2,
        time_bits=1,
    )
    samples = [1, 2]
    counts = {
        "001": 50,
        "110": 50,
    }

    metrics = evaluate_noisy_counts(counts, spec, samples)

    assert metrics["coverage_fraction"] == 1.0
    assert metrics["modal_amplitude_accuracy"] == 1.0
    assert metrics["correct_basis_shot_fraction"] == 1.0
    assert metrics["amplitude_bit_error_rate"] == 0.0
    assert metrics["exact_reconstruction"] is True


def test_small_ideal_aer_case_runs() -> None:
    compiled, spec, samples = prepare_noise_benchmark_circuit(
        num_samples=2,
        amplitude_bits=2,
        data_seed=42,
        optimization_level=0,
    )
    condition = NoiseCondition(
        family="ideal",
        severity="ideal",
        severity_index=0,
    )

    row = simulate_noise_case(
        compiled_circuit=compiled,
        spec=spec,
        samples=samples,
        condition=condition,
        shots=128,
        seed_simulator=42,
    )

    assert row["shots"] == 128
    assert row["coverage_fraction"] == 1.0
    assert row["exact_reconstruction"] is True


def test_aggregation_reports_rates_and_metric_statistics() -> None:
    rows = [
        {
            "num_samples": 4,
            "family": "gate",
            "severity": "low",
            "severity_index": 1,
            "single_qubit_error": 0.001,
            "two_qubit_error": 0.01,
            "readout_error": 0.0,
            "amplitude_bits": 4,
            "time_bits": 2,
            "total_qubits": 6,
            "shots": 128,
            "transpiled_depth": 100,
            "transpiled_size": 120,
            "transpiled_cx_count": 40,
            "exact_reconstruction": True,
            "coverage_fraction": 1.0,
            "modal_amplitude_accuracy": 1.0,
            "normalized_modal_mae": 0.0,
            "correct_basis_shot_fraction": 0.9,
            "amplitude_bit_error_rate": 0.02,
            "joint_distribution_tvd": 0.1,
            "time_distribution_tvd": 0.05,
            "simulation_seconds": 0.2,
        },
        {
            "num_samples": 4,
            "family": "gate",
            "severity": "low",
            "severity_index": 1,
            "single_qubit_error": 0.001,
            "two_qubit_error": 0.01,
            "readout_error": 0.0,
            "amplitude_bits": 4,
            "time_bits": 2,
            "total_qubits": 6,
            "shots": 128,
            "transpiled_depth": 100,
            "transpiled_size": 120,
            "transpiled_cx_count": 40,
            "exact_reconstruction": False,
            "coverage_fraction": 1.0,
            "modal_amplitude_accuracy": 0.75,
            "normalized_modal_mae": 0.1,
            "correct_basis_shot_fraction": 0.7,
            "amplitude_bit_error_rate": 0.08,
            "joint_distribution_tvd": 0.3,
            "time_distribution_tvd": 0.1,
            "simulation_seconds": 0.3,
        },
    ]

    summary = aggregate_noise_sensitivity_rows(rows)[0]

    assert summary["runs"] == 2
    assert summary["exact_reconstruction_rate"] == 0.5
    assert summary["modal_amplitude_accuracy_mean"] == pytest.approx(0.875)
    assert summary["correct_basis_shot_fraction_mean"] == pytest.approx(0.8)
