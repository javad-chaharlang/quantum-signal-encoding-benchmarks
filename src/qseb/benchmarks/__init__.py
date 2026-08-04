"""Reusable benchmark utilities for quantum signal encodings."""

from qseb.benchmarks.noise_sensitivity import (
    NoiseCondition,
    aggregate_noise_sensitivity_rows,
    build_noise_model,
    evaluate_noisy_counts,
    prepare_noise_benchmark_circuit,
    run_noise_sensitivity,
    simulate_noise_case,
)
from qseb.benchmarks.resource_scaling import (
    aggregate_resource_rows,
    benchmark_resource_case,
    generate_deterministic_samples,
    generate_profile_samples,
    run_amplitude_resolution_scaling,
    run_signal_length_scaling,
)
from qseb.benchmarks.shot_sensitivity import (
    aggregate_shot_sensitivity_rows,
    expected_coverage_fraction,
    expected_missing_indices,
    full_coverage_probability,
    minimum_shots_for_probability,
    run_shot_sensitivity,
    simulate_ideal_shot_case,
    validate_qiskit_shot_case,
)

__all__ = [
    "NoiseCondition",
    "aggregate_noise_sensitivity_rows",
    "aggregate_resource_rows",
    "aggregate_shot_sensitivity_rows",
    "benchmark_resource_case",
    "build_noise_model",
    "evaluate_noisy_counts",
    "expected_coverage_fraction",
    "expected_missing_indices",
    "full_coverage_probability",
    "generate_deterministic_samples",
    "generate_profile_samples",
    "minimum_shots_for_probability",
    "prepare_noise_benchmark_circuit",
    "run_amplitude_resolution_scaling",
    "run_noise_sensitivity",
    "run_shot_sensitivity",
    "run_signal_length_scaling",
    "simulate_ideal_shot_case",
    "simulate_noise_case",
    "validate_qiskit_shot_case",
]
