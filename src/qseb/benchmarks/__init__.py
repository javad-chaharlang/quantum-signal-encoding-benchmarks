"""Reusable benchmark utilities for quantum signal encodings."""

from qseb.benchmarks.hardware_noise import (
    CalibrationNoiseCondition,
    aggregate_hardware_noise_rows,
    backend_calibration_rows,
    build_calibration_noise_model,
    prepare_hardware_noise_circuit,
    run_calibration_hardware_noise,
    simulate_calibration_noise_case,
)
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
    "CalibrationNoiseCondition",
    "NoiseCondition",
    "aggregate_hardware_noise_rows",
    "aggregate_noise_sensitivity_rows",
    "aggregate_resource_rows",
    "aggregate_shot_sensitivity_rows",
    "backend_calibration_rows",
    "benchmark_resource_case",
    "build_calibration_noise_model",
    "build_noise_model",
    "evaluate_noisy_counts",
    "expected_coverage_fraction",
    "expected_missing_indices",
    "full_coverage_probability",
    "generate_deterministic_samples",
    "generate_profile_samples",
    "minimum_shots_for_probability",
    "prepare_hardware_noise_circuit",
    "prepare_noise_benchmark_circuit",
    "run_amplitude_resolution_scaling",
    "run_calibration_hardware_noise",
    "run_noise_sensitivity",
    "run_shot_sensitivity",
    "run_signal_length_scaling",
    "simulate_calibration_noise_case",
    "simulate_ideal_shot_case",
    "simulate_noise_case",
    "validate_qiskit_shot_case",
]
