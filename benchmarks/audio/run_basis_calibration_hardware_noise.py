"""Run calibration-derived hardware-noise simulations."""

from __future__ import annotations

import csv
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit_ibm_runtime.fake_provider import FakeNairobiV2

from qseb.benchmarks import (
    CalibrationNoiseCondition,
    aggregate_hardware_noise_rows,
    backend_calibration_rows,
    run_calibration_hardware_noise,
)

SAMPLE_COUNTS = (4, 8)
AMPLITUDE_BITS = 4
SHOTS = 2048
DATA_SEED = 42
OPTIMIZATION_LEVEL = 2
LAYOUT_SEEDS = (42, 52, 62, 72, 82)
SIMULATOR_SEEDS = (42, 52, 62)

CONDITIONS = (
    CalibrationNoiseCondition(
        name="ideal",
        gate_error=False,
        readout_error=False,
        thermal_relaxation=False,
    ),
    CalibrationNoiseCondition(
        name="readout_only",
        gate_error=False,
        readout_error=True,
        thermal_relaxation=False,
    ),
    CalibrationNoiseCondition(
        name="gate_thermal",
        gate_error=True,
        readout_error=False,
        thermal_relaxation=True,
    ),
    CalibrationNoiseCondition(
        name="full_calibration",
        gate_error=True,
        readout_error=True,
        thermal_relaxation=True,
    ),
)

CONDITION_ORDER = tuple(condition.name for condition in CONDITIONS)
CONDITION_LABELS = (
    "Ideal",
    "Readout only",
    "Gate + thermal",
    "Full calibration",
)

EXPECTED_RAW_RUNS = len(SAMPLE_COUNTS) * len(LAYOUT_SEEDS) * len(CONDITIONS) * len(SIMULATOR_SEEDS)

RESULT_DIR = Path("results/audio/hardware_noise")
FIGURE_DIR = Path("figures/audio/hardware_noise")


def _package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"


def _environment_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "qiskit": _package_version("qiskit"),
        "qiskit_aer": _package_version("qiskit-aer"),
        "qiskit_ibm_runtime": _package_version("qiskit-ibm-runtime"),
        "numpy": _package_version("numpy"),
        "matplotlib": _package_version("matplotlib"),
    }


def _ensure_output_directories() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv(
    rows: list[dict[str, object]],
    *,
    filename: str,
) -> Path:
    output_path = RESULT_DIR / filename
    fieldnames = list(rows[0])

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def _write_json(
    raw_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    layout_rows: list[dict[str, object]],
    calibration_rows: list[dict[str, object]],
) -> Path:
    report = {
        "benchmark": "basis_encoded_audio_calibration_hardware_noise",
        "environment": _environment_metadata(),
        "configuration": {
            "backend_class": "FakeNairobiV2",
            "backend_snapshot": True,
            "live_backend_calibration": False,
            "hardware_execution": False,
            "sample_counts": list(SAMPLE_COUNTS),
            "amplitude_bits": AMPLITUDE_BITS,
            "shots": SHOTS,
            "data_seed": DATA_SEED,
            "optimization_level": OPTIMIZATION_LEVEL,
            "layout_seeds": list(LAYOUT_SEEDS),
            "simulator_seeds": list(SIMULATOR_SEEDS),
            "conditions": [
                {
                    "name": condition.name,
                    "gate_error": condition.gate_error,
                    "readout_error": condition.readout_error,
                    "thermal_relaxation": condition.thermal_relaxation,
                }
                for condition in CONDITIONS
            ],
        },
        "summary": summary_rows,
        "layout_summary": layout_rows,
        "backend_calibration": calibration_rows,
        "raw_runs": raw_rows,
    }

    output_path = RESULT_DIR / "hardware_noise.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _rows_for_samples(
    summary_rows: list[dict[str, object]],
    num_samples: int,
) -> list[dict[str, object]]:
    lookup = {
        str(row["condition"]): row for row in summary_rows if int(row["num_samples"]) == num_samples
    }
    return [lookup[condition] for condition in CONDITION_ORDER]


def _plot_metric(
    summary_rows: list[dict[str, object]],
    *,
    metric: str,
    y_label: str,
    title: str,
    filename: str,
    ylim: tuple[float, float] | None = None,
) -> Path:
    figure, axis = plt.subplots(figsize=(9.5, 5.7))
    x_values = list(range(len(CONDITION_ORDER)))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        means = [float(row[f"{metric}_mean"]) for row in rows]
        standard_deviations = [float(row[f"{metric}_std"]) for row in rows]

        axis.errorbar(
            x_values,
            means,
            yerr=standard_deviations,
            marker="o",
            capsize=3,
            label=f"N={num_samples}",
        )

    axis.set_xlabel("Calibration-derived noise model")
    axis.set_ylabel(y_label)
    axis.set_title(title)
    axis.set_xticks(x_values, CONDITION_LABELS)
    if ylim is not None:
        axis.set_ylim(*ylim)
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    output_path = FIGURE_DIR / filename
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_exact_reconstruction(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.5, 5.7))
    x_values = list(range(len(CONDITION_ORDER)))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        rates = [float(row["exact_reconstruction_rate"]) for row in rows]
        lower = [
            max(
                0.0,
                rates[index] - float(rows[index]["exact_rate_wilson_95_low"]),
            )
            for index in range(len(rows))
        ]
        upper = [
            max(
                0.0,
                float(rows[index]["exact_rate_wilson_95_high"]) - rates[index],
            )
            for index in range(len(rows))
        ]

        axis.errorbar(
            x_values,
            rates,
            yerr=[lower, upper],
            marker="o",
            capsize=3,
            label=f"N={num_samples}",
        )

    axis.set_xlabel("Calibration-derived noise model")
    axis.set_ylabel("Exact reconstruction rate")
    axis.set_title("Exact Reconstruction under Snapshot-Derived Noise")
    axis.set_xticks(x_values, CONDITION_LABELS)
    axis.set_ylim(-0.03, 1.03)
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    output_path = FIGURE_DIR / "exact_reconstruction_rate.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_layout_sensitivity(
    layout_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.5, 5.7))

    for num_samples in SAMPLE_COUNTS:
        rows = [
            row
            for row in layout_rows
            if int(row["num_samples"]) == num_samples and row["condition"] == "full_calibration"
        ]
        x_values = [float(row["independent_gate_success_proxy_mean"]) for row in rows]
        y_values = [float(row["correct_basis_shot_fraction_mean"]) for row in rows]

        axis.scatter(
            x_values,
            y_values,
            label=f"N={num_samples}",
        )

        for row, x_value, y_value in zip(
            rows,
            x_values,
            y_values,
            strict=True,
        ):
            axis.annotate(
                str(row["seed_transpiler"]),
                (x_value, y_value),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
            )

    axis.set_xlabel("Independent calibrated-gate success proxy")
    axis.set_ylabel("Mean correct basis-state fraction")
    axis.set_title("Layout Sensitivity under Full Snapshot-Derived Noise")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    output_path = FIGURE_DIR / "layout_sensitivity.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _selected_table(
    summary_rows: list[dict[str, object]],
) -> str:
    lines = [
        (
            "| Samples | Condition | Exact rate | Modal accuracy | "
            "Correct-state fraction | Amplitude BER | Joint TVD |"
        ),
        "|---:|:---|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["num_samples"]),
                    str(row["condition"]),
                    f"{float(row['exact_reconstruction_rate']):.3f}",
                    f"{float(row['modal_amplitude_accuracy_mean']):.3f}",
                    f"{float(row['correct_basis_shot_fraction_mean']):.3f}",
                    f"{float(row['amplitude_bit_error_rate_mean']):.4f}",
                    f"{float(row['joint_distribution_tvd_mean']):.3f}",
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _write_markdown(
    summary_rows: list[dict[str, object]],
) -> Path:
    selected_table = _selected_table(summary_rows)

    text = f"""# Calibration-Derived Hardware-Noise Benchmark

## Reproducibility boundary

This experiment uses `FakeNairobiV2`, a seven-qubit historical backend snapshot from
`qiskit-ibm-runtime`. The snapshot contains backend topology and calibration-derived
qubit and instruction properties. It is not a live calibration and is not a real
hardware execution.

## Configuration

- Signal lengths: `{list(SAMPLE_COUNTS)}`
- Amplitude width: `{AMPLITUDE_BITS}` qubits
- Shots per run: `{SHOTS}`
- Layout seeds: `{list(LAYOUT_SEEDS)}`
- Simulator seeds: `{list(SIMULATOR_SEEDS)}`
- Optimization level: `{OPTIMIZATION_LEVEL}`
- Conditions: `{list(CONDITION_ORDER)}`
- Expected raw runs: `{EXPECTED_RAW_RUNS}`

## Selected results

{selected_table}

## Figures

![Exact reconstruction](../../../figures/audio/hardware_noise/exact_reconstruction_rate.png)

![Correct states](../../../figures/audio/hardware_noise/correct_basis_shot_fraction.png)

![Modal accuracy](../../../figures/audio/hardware_noise/modal_amplitude_accuracy.png)

![Joint TVD](../../../figures/audio/hardware_noise/joint_distribution_tvd.png)

![Layout sensitivity](../../../figures/audio/hardware_noise/layout_sensitivity.png)

## Machine-readable outputs

- `hardware_noise_runs.csv`
- `hardware_noise_summary.csv`
- `hardware_noise_layout_summary.csv`
- `backend_calibration.csv`
- `hardware_noise.json`
"""

    output_path = RESULT_DIR / "README.md"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def main() -> None:
    _ensure_output_directories()
    backend = FakeNairobiV2()

    print("Running calibration-derived hardware-noise benchmark...")
    raw_rows = run_calibration_hardware_noise(
        backend,
        sample_counts=SAMPLE_COUNTS,
        conditions=CONDITIONS,
        layout_seeds=LAYOUT_SEEDS,
        simulator_seeds=SIMULATOR_SEEDS,
        amplitude_bits=AMPLITUDE_BITS,
        shots=SHOTS,
        data_seed=DATA_SEED,
        optimization_level=OPTIMIZATION_LEVEL,
    )
    summary_rows = aggregate_hardware_noise_rows(
        raw_rows,
        by_layout=False,
    )
    layout_rows = aggregate_hardware_noise_rows(
        raw_rows,
        by_layout=True,
    )
    calibration_rows = backend_calibration_rows(backend)

    generated_paths = [
        _write_csv(
            raw_rows,
            filename="hardware_noise_runs.csv",
        ),
        _write_csv(
            summary_rows,
            filename="hardware_noise_summary.csv",
        ),
        _write_csv(
            layout_rows,
            filename="hardware_noise_layout_summary.csv",
        ),
        _write_csv(
            calibration_rows,
            filename="backend_calibration.csv",
        ),
        _write_json(
            raw_rows,
            summary_rows,
            layout_rows,
            calibration_rows,
        ),
        _write_markdown(summary_rows),
        _plot_exact_reconstruction(summary_rows),
        _plot_metric(
            summary_rows,
            metric="correct_basis_shot_fraction",
            y_label="Mean correct basis-state fraction",
            title="Correct Basis States under Snapshot-Derived Noise",
            filename="correct_basis_shot_fraction.png",
            ylim=(-0.03, 1.03),
        ),
        _plot_metric(
            summary_rows,
            metric="modal_amplitude_accuracy",
            y_label="Mean modal amplitude accuracy",
            title="Modal Accuracy under Snapshot-Derived Noise",
            filename="modal_amplitude_accuracy.png",
            ylim=(-0.03, 1.03),
        ),
        _plot_metric(
            summary_rows,
            metric="joint_distribution_tvd",
            y_label="Mean joint-distribution TVD",
            title="Joint Distribution Deviation under Snapshot Noise",
            filename="joint_distribution_tvd.png",
            ylim=(0.0, 1.0),
        ),
        _plot_layout_sensitivity(layout_rows),
    ]

    print("Generated calibration-derived assets:")
    for path in generated_paths:
        print(f"  - {path}")

    print(f"Raw hardware-noise runs: {len(raw_rows)}")
    print(f"Aggregated conditions: {len(summary_rows)}")
    print(f"Layout-level conditions: {len(layout_rows)}")
    print(f"Calibration records: {len(calibration_rows)}")


if __name__ == "__main__":
    main()
