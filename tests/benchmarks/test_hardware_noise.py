"""Tests for calibration-derived hardware-noise utilities."""

from __future__ import annotations

import pytest
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeNairobiV2

from qseb.benchmarks import (
    CalibrationNoiseCondition,
    aggregate_hardware_noise_rows,
    backend_calibration_rows,
    build_calibration_noise_model,
    prepare_hardware_noise_circuit,
    simulate_calibration_noise_case,
)


def _ideal_condition() -> CalibrationNoiseCondition:
    return CalibrationNoiseCondition(
        name="ideal",
        gate_error=False,
        readout_error=False,
        thermal_relaxation=False,
    )


def test_condition_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CalibrationNoiseCondition(
            name="",
            gate_error=False,
            readout_error=False,
            thermal_relaxation=False,
        )


def test_ideal_condition_has_no_noise_model() -> None:
    backend = FakeNairobiV2()
    condition = _ideal_condition()

    assert condition.is_ideal
    assert build_calibration_noise_model(backend, condition) is None


def test_readout_condition_builds_snapshot_model() -> None:
    backend = FakeNairobiV2()
    condition = CalibrationNoiseCondition(
        name="readout_only",
        gate_error=False,
        readout_error=True,
        thermal_relaxation=False,
    )

    model = build_calibration_noise_model(backend, condition)

    assert model is not None
    assert not model.is_ideal()


def test_backend_calibration_rows_include_qubits_and_instructions() -> None:
    rows = backend_calibration_rows(FakeNairobiV2())
    qubit_rows = [row for row in rows if row["record_type"] == "qubit"]

    assert len(qubit_rows) == 7
    assert any(row["record_type"] == "instruction" for row in rows)
    assert any(row["instruction_error"] is not None for row in qubit_rows)


def test_prepare_small_hardware_mapped_circuit() -> None:
    compiled, spec, samples, metadata = prepare_hardware_noise_circuit(
        FakeNairobiV2(),
        num_samples=2,
        amplitude_bits=2,
        data_seed=42,
        optimization_level=1,
        seed_transpiler=42,
    )

    assert spec.total_qubits == 3
    assert len(samples) == 2
    assert compiled.num_clbits == 3
    assert metadata["transpiled_depth"] > 0
    assert len(str(metadata["initial_layout"]).split("-")) == 3


def test_small_ideal_simulation_runs() -> None:
    backend = FakeNairobiV2()
    compiled, spec, samples, _ = prepare_hardware_noise_circuit(
        backend,
        num_samples=2,
        amplitude_bits=2,
        data_seed=42,
        optimization_level=1,
        seed_transpiler=42,
    )

    row = simulate_calibration_noise_case(
        simulator=AerSimulator(),
        compiled_circuit=compiled,
        spec=spec,
        samples=samples,
        condition=_ideal_condition(),
        shots=128,
        seed_simulator=42,
    )

    assert row["shots"] == 128
    assert 0.0 <= row["correct_basis_shot_fraction"] <= 1.0
    assert row["coverage_fraction"] == 1.0


def test_aggregation_supports_global_and_layout_views() -> None:
    base = {
        "backend_name": "fake_nairobi",
        "backend_class": "FakeNairobiV2",
        "num_samples": 4,
        "condition": "full_calibration",
        "shots": 128,
        "amplitude_bits": 4,
        "time_bits": 2,
        "logical_qubits": 6,
        "gate_error_enabled": True,
        "readout_error_enabled": True,
        "thermal_relaxation_enabled": True,
        "seed_transpiler": 42,
        "initial_layout": "0-1-2-3-4-5",
        "final_layout": "0-1-2-3-4-5",
        "exact_reconstruction": True,
        "coverage_fraction": 1.0,
        "modal_amplitude_accuracy": 1.0,
        "normalized_modal_mae": 0.0,
        "correct_basis_shot_fraction": 0.8,
        "amplitude_bit_error_rate": 0.05,
        "joint_distribution_tvd": 0.2,
        "time_distribution_tvd": 0.04,
        "simulation_seconds": 0.1,
        "transpiled_depth": 100,
        "transpiled_size": 120,
        "two_qubit_gate_count": 40,
        "swap_count": 0,
        "calibrated_gate_count": 100,
        "missing_calibration_count": 0,
        "calibration_error_budget": 0.5,
        "independent_gate_success_proxy": 0.6,
        "calibrated_duration_seconds": 0.0001,
        "selected_readout_error_mean": 0.02,
        "selected_readout_error_max": 0.03,
        "selected_t1_seconds_mean": 0.0001,
        "selected_t2_seconds_mean": 0.00008,
    }
    second = {
        **base,
        "exact_reconstruction": False,
        "modal_amplitude_accuracy": 0.75,
        "correct_basis_shot_fraction": 0.6,
    }

    global_summary = aggregate_hardware_noise_rows(
        [base, second],
        by_layout=False,
    )[0]
    layout_summary = aggregate_hardware_noise_rows(
        [base, second],
        by_layout=True,
    )[0]

    assert global_summary["runs"] == 2
    assert global_summary["exact_reconstruction_rate"] == 0.5
    assert global_summary["correct_basis_shot_fraction_mean"] == pytest.approx(0.7)
    assert layout_summary["seed_transpiler"] == 42
