"""Run a controlled synthetic-noise benchmark for basis-encoded audio."""

from __future__ import annotations

import csv
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib.pyplot as plt

from qseb.benchmarks import (
    NoiseCondition,
    aggregate_noise_sensitivity_rows,
    run_noise_sensitivity,
)

SAMPLE_COUNTS = (4, 8)
AMPLITUDE_BITS = 4
SHOTS = 1024
SEEDS = (42, 52, 62, 72, 82)
DATA_SEED = 42
SEED_TRANSPILER = 42
OPTIMIZATION_LEVEL = 1

SEVERITY_LEVELS = (
    ("low", 1, 0.0005, 0.005, 0.005),
    ("moderate", 2, 0.001, 0.01, 0.01),
    ("high", 3, 0.002, 0.02, 0.02),
    ("severe", 4, 0.005, 0.05, 0.05),
)

FAMILIES = ("gate", "readout", "combined")
SEVERITY_LABELS = ("Ideal", "Low", "Moderate", "High", "Severe")

RESULT_DIR = Path("results/audio/noise_sensitivity")
FIGURE_DIR = Path("figures/audio/noise_sensitivity")


def _conditions() -> tuple[NoiseCondition, ...]:
    conditions = [
        NoiseCondition(
            family="ideal",
            severity="ideal",
            severity_index=0,
        )
    ]

    for severity, index, one_qubit, two_qubit, readout in SEVERITY_LEVELS:
        conditions.extend(
            [
                NoiseCondition(
                    family="gate",
                    severity=severity,
                    severity_index=index,
                    single_qubit_error=one_qubit,
                    two_qubit_error=two_qubit,
                ),
                NoiseCondition(
                    family="readout",
                    severity=severity,
                    severity_index=index,
                    readout_error=readout,
                ),
                NoiseCondition(
                    family="combined",
                    severity=severity,
                    severity_index=index,
                    single_qubit_error=one_qubit,
                    two_qubit_error=two_qubit,
                    readout_error=readout,
                ),
            ]
        )

    return tuple(conditions)


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
) -> Path:
    report = {
        "benchmark": "basis_encoded_quantum_audio_noise_sensitivity",
        "environment": _environment_metadata(),
        "configuration": {
            "sample_counts": list(SAMPLE_COUNTS),
            "amplitude_bits": AMPLITUDE_BITS,
            "shots": SHOTS,
            "seeds": list(SEEDS),
            "data_seed": DATA_SEED,
            "seed_transpiler": SEED_TRANSPILER,
            "optimization_level": OPTIMIZATION_LEVEL,
            "severity_levels": [
                {
                    "severity": severity,
                    "severity_index": index,
                    "single_qubit_error": one_qubit,
                    "two_qubit_error": two_qubit,
                    "readout_error": readout,
                }
                for severity, index, one_qubit, two_qubit, readout in SEVERITY_LEVELS
            ],
            "families": list(FAMILIES),
            "synthetic_noise": True,
            "backend_calibration_derived": False,
            "hardware_execution": False,
        },
        "summary": summary_rows,
        "raw_runs": raw_rows,
    }

    output_path = RESULT_DIR / "noise_sensitivity.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _ideal_row(
    rows: list[dict[str, object]],
    num_samples: int,
) -> dict[str, object]:
    return next(
        row for row in rows if int(row["num_samples"]) == num_samples and row["family"] == "ideal"
    )


def _family_rows(
    rows: list[dict[str, object]],
    num_samples: int,
    family: str,
) -> list[dict[str, object]]:
    ideal = _ideal_row(rows, num_samples)
    noisy = sorted(
        (row for row in rows if int(row["num_samples"]) == num_samples and row["family"] == family),
        key=lambda row: int(row["severity_index"]),
    )
    return [ideal, *noisy]


def _plot_metric(
    summary_rows: list[dict[str, object]],
    *,
    metric: str,
    y_label: str,
    title: str,
    filename: str,
    ylim: tuple[float, float] | None = None,
) -> Path:
    figure, axis = plt.subplots(figsize=(9.6, 5.8))

    for num_samples in SAMPLE_COUNTS:
        for family in FAMILIES:
            rows = _family_rows(
                summary_rows,
                num_samples,
                family,
            )
            x_values = [int(row["severity_index"]) for row in rows]
            means = [float(row[f"{metric}_mean"]) for row in rows]
            standard_deviations = [float(row[f"{metric}_std"]) for row in rows]

            axis.errorbar(
                x_values,
                means,
                yerr=standard_deviations,
                marker="o",
                capsize=3,
                label=f"N={num_samples} {family}",
            )

    axis.set_xlabel("Synthetic noise severity")
    axis.set_ylabel(y_label)
    axis.set_title(title)
    axis.set_xticks(range(len(SEVERITY_LABELS)), SEVERITY_LABELS)
    if ylim is not None:
        axis.set_ylim(*ylim)
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()

    output_path = FIGURE_DIR / filename
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_exact_reconstruction(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.6, 5.8))

    for num_samples in SAMPLE_COUNTS:
        for family in FAMILIES:
            rows = _family_rows(
                summary_rows,
                num_samples,
                family,
            )
            x_values = [int(row["severity_index"]) for row in rows]
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
                label=f"N={num_samples} {family}",
            )

    axis.set_xlabel("Synthetic noise severity")
    axis.set_ylabel("Exact reconstruction rate")
    axis.set_title("Exact Reconstruction under Synthetic Noise")
    axis.set_xticks(range(len(SEVERITY_LABELS)), SEVERITY_LABELS)
    axis.set_ylim(-0.03, 1.03)
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()

    output_path = FIGURE_DIR / "exact_reconstruction_rate.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _selected_table(
    summary_rows: list[dict[str, object]],
) -> str:
    lines = [
        (
            "| Samples | Family | Severity | Exact rate | Modal accuracy | "
            "Correct-shot fraction | Bit-error rate | Joint TVD |"
        ),
        "|---:|:---|:---|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        if row["severity"] not in {"ideal", "moderate", "severe"}:
            continue

        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["num_samples"]),
                    str(row["family"]),
                    str(row["severity"]),
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

    summary = f"""# Basis-Encoded Quantum Audio: Noise-Sensitivity Benchmark

## Scientific question

How do synthetic gate depolarization, symmetric readout error, and their combination
affect reconstruction of the current basis-encoded audio representation?

## Controlled configuration

- Signal lengths: `{list(SAMPLE_COUNTS)}`
- Amplitude width: `{AMPLITUDE_BITS}` qubits
- Shots per run: `{SHOTS}`
- Simulator seeds: `{list(SEEDS)}`
- Noise families: `{list(FAMILIES)}`
- Severity levels: `{list(SEVERITY_LABELS)}`
- `RZ` treated as ideal
- One-qubit depolarizing error applied to `SX` and `X`
- Two-qubit depolarizing error applied to `CX`
- Symmetric readout error applied to every measured qubit
- Synthetic parameters; not derived from a backend calibration
- Hardware execution: `False`

## Selected results

{selected_table}

## Figures

![Exact reconstruction](../../../figures/audio/noise_sensitivity/exact_reconstruction_rate.png)

![Modal amplitude accuracy](../../../figures/audio/noise_sensitivity/modal_amplitude_accuracy.png)

![Correct shots](../../../figures/audio/noise_sensitivity/correct_basis_shot_fraction.png)

![Amplitude bit-error rate](../../../figures/audio/noise_sensitivity/amplitude_bit_error_rate.png)

![Joint-distribution TVD](../../../figures/audio/noise_sensitivity/joint_distribution_tvd.png)

## Interpretation boundary

The configured error probabilities are controlled synthetic stress tests. They do
not reproduce a specific IBM Quantum backend, connectivity graph, calibration
snapshot, thermal-relaxation profile, or drift process.

Machine-readable outputs:

- `results/audio/noise_sensitivity/noise_sensitivity_runs.csv`
- `results/audio/noise_sensitivity/noise_sensitivity_summary.csv`
- `results/audio/noise_sensitivity/noise_sensitivity.json`
"""

    output_path = RESULT_DIR / "README.md"
    output_path.write_text(summary, encoding="utf-8")
    return output_path


def main() -> None:
    _ensure_output_directories()
    conditions = _conditions()

    print("Running controlled synthetic-noise benchmark...")
    raw_rows = run_noise_sensitivity(
        sample_counts=SAMPLE_COUNTS,
        conditions=conditions,
        seeds=SEEDS,
        amplitude_bits=AMPLITUDE_BITS,
        shots=SHOTS,
        data_seed=DATA_SEED,
        optimization_level=OPTIMIZATION_LEVEL,
        seed_transpiler=SEED_TRANSPILER,
    )
    summary_rows = aggregate_noise_sensitivity_rows(raw_rows)

    generated_paths = [
        _write_csv(
            raw_rows,
            filename="noise_sensitivity_runs.csv",
        ),
        _write_csv(
            summary_rows,
            filename="noise_sensitivity_summary.csv",
        ),
        _write_json(raw_rows, summary_rows),
        _write_markdown(summary_rows),
        _plot_exact_reconstruction(summary_rows),
        _plot_metric(
            summary_rows,
            metric="modal_amplitude_accuracy",
            y_label="Mean modal amplitude accuracy",
            title="Modal Amplitude Accuracy under Synthetic Noise",
            filename="modal_amplitude_accuracy.png",
            ylim=(-0.03, 1.03),
        ),
        _plot_metric(
            summary_rows,
            metric="correct_basis_shot_fraction",
            y_label="Mean correct basis-shot fraction",
            title="Correct Basis-State Fraction under Synthetic Noise",
            filename="correct_basis_shot_fraction.png",
            ylim=(-0.03, 1.03),
        ),
        _plot_metric(
            summary_rows,
            metric="amplitude_bit_error_rate",
            y_label="Mean amplitude bit-error rate",
            title="Amplitude Bit-Error Rate under Synthetic Noise",
            filename="amplitude_bit_error_rate.png",
            ylim=(0.0, 0.5),
        ),
        _plot_metric(
            summary_rows,
            metric="joint_distribution_tvd",
            y_label="Mean joint-distribution TVD",
            title="Joint Distribution Deviation under Synthetic Noise",
            filename="joint_distribution_tvd.png",
            ylim=(0.0, 1.0),
        ),
    ]

    print("Generated noise-sensitivity assets:")
    for path in generated_paths:
        print(f"  - {path}")

    print(f"Raw noisy runs: {len(raw_rows)}")
    print(f"Aggregated noise conditions: {len(summary_rows)}")


if __name__ == "__main__":
    main()
