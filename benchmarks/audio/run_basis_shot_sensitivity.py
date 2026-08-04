"""Run a controlled shot-sensitivity benchmark for basis-encoded audio."""

from __future__ import annotations

import csv
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib.pyplot as plt

from qseb.benchmarks import (
    aggregate_shot_sensitivity_rows,
    minimum_shots_for_probability,
    run_shot_sensitivity,
    validate_qiskit_shot_case,
)

SAMPLE_COUNTS = (4, 8, 16, 32)
SHOT_COUNTS = (
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
)
SEEDS = tuple(42 + (10 * index) for index in range(50))
AMPLITUDE_BITS = 4
QISKIT_VALIDATION_CASES = (
    (4, 256),
    (8, 1024),
)

RESULT_DIR = Path("results/audio/shot_sensitivity")
FIGURE_DIR = Path("figures/audio/shot_sensitivity")


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


def _threshold_rows() -> list[dict[str, object]]:
    return [
        {
            "num_samples": num_samples,
            "shots_for_95_percent_full_coverage": (
                minimum_shots_for_probability(num_samples, 0.95)
            ),
            "shots_for_99_percent_full_coverage": (
                minimum_shots_for_probability(num_samples, 0.99)
            ),
        }
        for num_samples in SAMPLE_COUNTS
    ]


def _write_json(
    raw_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    qiskit_validation: list[dict[str, object]],
    threshold_rows: list[dict[str, object]],
) -> Path:
    report = {
        "benchmark": "basis_encoded_quantum_audio_shot_sensitivity",
        "environment": _environment_metadata(),
        "configuration": {
            "sample_counts": list(SAMPLE_COUNTS),
            "shot_counts": list(SHOT_COUNTS),
            "seeds": list(SEEDS),
            "num_monte_carlo_seeds": len(SEEDS),
            "amplitude_bits": AMPLITUDE_BITS,
            "ideal_sampling_model": (
                "uniform time-index multinomial derived from the exact "
                "basis-encoded state"
            ),
            "qiskit_validation_cases": [
                {
                    "num_samples": num_samples,
                    "shots": shots,
                }
                for num_samples, shots in QISKIT_VALIDATION_CASES
            ],
            "noise_model": None,
            "hardware_execution": False,
        },
        "thresholds": threshold_rows,
        "qiskit_validation": qiskit_validation,
        "summary": summary_rows,
        "raw_runs": raw_rows,
    }

    output_path = RESULT_DIR / "shot_sensitivity.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _rows_for_samples(
    summary_rows: list[dict[str, object]],
    num_samples: int,
) -> list[dict[str, object]]:
    return sorted(
        (
            row
            for row in summary_rows
            if int(row["num_samples"]) == num_samples
        ),
        key=lambda row: int(row["shots"]),
    )


def _plot_exact_reconstruction(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.4, 5.6))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        shots = [int(row["shots"]) for row in rows]
        empirical = [
            float(row["empirical_exact_reconstruction_rate"])
            for row in rows
        ]
        theoretical = [
            float(row["theoretical_full_coverage_probability"])
            for row in rows
        ]

        # Floating-point rounding can occasionally produce a tiny negative
        # difference (for example, -1e-17) even though a Wilson interval
        # mathematically contains the empirical estimate. Matplotlib rejects
        # negative y-error values, so clamp those numerical artifacts to zero.
        lower_errors = [
            max(
                0.0,
                empirical[index]
                - float(rows[index]["exact_rate_wilson_95_low"]),
            )
            for index in range(len(rows))
        ]
        upper_errors = [
            max(
                0.0,
                float(rows[index]["exact_rate_wilson_95_high"])
                - empirical[index],
            )
            for index in range(len(rows))
        ]

        axis.errorbar(
            shots,
            empirical,
            yerr=[lower_errors, upper_errors],
            marker="o",
            capsize=3,
            label=f"N={num_samples} empirical",
        )
        axis.plot(
            shots,
            theoretical,
            linestyle="--",
            marker="x",
            label=f"N={num_samples} theory",
        )

    axis.set_xscale("log", base=2)
    axis.set_xlabel("Number of shots")
    axis.set_ylabel("Probability of exact reconstruction")
    axis.set_title("Exact Reconstruction versus Measurement Shots")
    axis.set_ylim(-0.03, 1.03)
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()

    output_path = FIGURE_DIR / "exact_reconstruction_probability.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_coverage(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.4, 5.6))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        shots = [int(row["shots"]) for row in rows]
        empirical = [
            float(row["coverage_fraction_mean"]) for row in rows
        ]
        theoretical = [
            float(row["theoretical_expected_coverage_fraction"])
            for row in rows
        ]

        axis.plot(
            shots,
            empirical,
            marker="o",
            label=f"N={num_samples} empirical",
        )
        axis.plot(
            shots,
            theoretical,
            linestyle="--",
            label=f"N={num_samples} theory",
        )

    axis.set_xscale("log", base=2)
    axis.set_xlabel("Number of shots")
    axis.set_ylabel("Mean observed-index coverage")
    axis.set_title("Time-Index Coverage versus Measurement Shots")
    axis.set_ylim(-0.03, 1.03)
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()

    output_path = FIGURE_DIR / "mean_time_index_coverage.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_missing_indices(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.4, 5.6))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        shots = [int(row["shots"]) for row in rows]
        empirical = [
            float(row["missing_indices_mean"]) for row in rows
        ]
        theoretical = [
            float(row["theoretical_expected_missing_indices"])
            for row in rows
        ]

        axis.plot(
            shots,
            empirical,
            marker="o",
            label=f"N={num_samples} empirical",
        )
        axis.plot(
            shots,
            theoretical,
            linestyle="--",
            label=f"N={num_samples} theory",
        )

    axis.set_xscale("log", base=2)
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel("Number of shots")
    axis.set_ylabel("Mean missing time indices")
    axis.set_title("Unobserved Time Indices versus Measurement Shots")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()

    output_path = FIGURE_DIR / "mean_missing_time_indices.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _plot_tvd(
    summary_rows: list[dict[str, object]],
) -> Path:
    figure, axis = plt.subplots(figsize=(9.4, 5.6))

    for num_samples in SAMPLE_COUNTS:
        rows = _rows_for_samples(summary_rows, num_samples)
        shots = [int(row["shots"]) for row in rows]
        tvd = [float(row["time_distribution_tvd_mean"]) for row in rows]

        axis.plot(
            shots,
            tvd,
            marker="o",
            label=f"N={num_samples}",
        )

    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlabel("Number of shots")
    axis.set_ylabel("Mean total variation distance")
    axis.set_title("Empirical Time Distribution versus Uniform Target")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    output_path = FIGURE_DIR / "time_distribution_tvd.png"
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _format_probability(value: object) -> str:
    return f"{float(value):.4f}"


def _threshold_markdown(
    threshold_rows: list[dict[str, object]],
) -> str:
    lines = [
        "| Samples | Shots for ≥95% full coverage | Shots for ≥99% full coverage |",
        "|---:|---:|---:|",
    ]

    for row in threshold_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["num_samples"]),
                    str(row["shots_for_95_percent_full_coverage"]),
                    str(row["shots_for_99_percent_full_coverage"]),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _selected_summary_markdown(
    summary_rows: list[dict[str, object]],
) -> str:
    selected_shots = (32, 64, 128, 256)
    lines = [
        (
            "| Samples | Shots | Empirical exact rate | Theory | "
            "Mean coverage | Mean missing |"
        ),
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        if int(row["shots"]) not in selected_shots:
            continue

        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["num_samples"]),
                    str(row["shots"]),
                    _format_probability(
                        row["empirical_exact_reconstruction_rate"]
                    ),
                    _format_probability(
                        row["theoretical_full_coverage_probability"]
                    ),
                    _format_probability(row["coverage_fraction_mean"]),
                    f"{float(row['missing_indices_mean']):.3f}",
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _write_markdown(
    summary_rows: list[dict[str, object]],
    qiskit_validation: list[dict[str, object]],
    threshold_rows: list[dict[str, object]],
) -> Path:
    thresholds = _threshold_markdown(threshold_rows)
    selected_summary = _selected_summary_markdown(summary_rows)

    validation_lines = [
        "| Samples | Shots | Coverage | Observed amplitudes correct | Exact reconstruction |",
        "|---:|---:|---:|:---:|:---:|",
    ]
    for row in qiskit_validation:
        validation_lines.append(
            "| "
            + " | ".join(
                [
                    str(row["num_samples"]),
                    str(row["shots"]),
                    f"{float(row['coverage_fraction']):.4f}",
                    str(row["observed_amplitudes_correct"]),
                    str(row["exact_reconstruction"]),
                ]
            )
            + " |"
        )
    validation_table = "\n".join(validation_lines)

    summary = f"""# Basis-Encoded Quantum Audio: Shot-Sensitivity Benchmark

## Scientific question

How many measurement shots are required to observe every time index and reconstruct
the complete basis-encoded signal under ideal noiseless sampling?

## Key property of the present encoding

The time register is uniform, so every one of the `N` time indices has probability
`1/N`. Once a time index is observed, its corresponding basis-encoded amplitude is
deterministic. Under ideal sampling, exact reconstruction is therefore equivalent
to observing all time indices at least once.

## Controlled configuration

- Signal lengths: `{list(SAMPLE_COUNTS)}`
- Shot counts: `{list(SHOT_COUNTS)}`
- Monte Carlo seeds: `{len(SEEDS)}`
- Fixed amplitude width for Qiskit validation: `{AMPLITUDE_BITS}` qubits
- Noise model: `None`
- Hardware execution: `False`
- Theoretical reference: exact uniform coupon-coverage dynamic program

## Theoretical shot thresholds

{thresholds}

## Selected empirical and theoretical results

{selected_summary}

## Actual Qiskit encode-measure-decode validation

{validation_table}

## Figures

![Plot](../../../figures/audio/shot_sensitivity/exact_reconstruction_probability.png)

![Mean time-index coverage](../../../figures/audio/shot_sensitivity/mean_time_index_coverage.png)

![Mean missing time indices](../../../figures/audio/shot_sensitivity/mean_missing_time_indices.png)

![Time-distribution TVD](../../../figures/audio/shot_sensitivity/time_distribution_tvd.png)

## Interpretation boundary

This benchmark isolates finite-shot sampling under an ideal noiseless model. It does
not include gate errors, readout errors, backend topology, or hardware drift. Noise
sensitivity is a separate experiment.

Machine-readable outputs:

- `results/audio/shot_sensitivity/shot_sensitivity_runs.csv`
- `results/audio/shot_sensitivity/shot_sensitivity_summary.csv`
- `results/audio/shot_sensitivity/shot_sensitivity.json`
"""

    output_path = RESULT_DIR / "README.md"
    output_path.write_text(summary, encoding="utf-8")
    return output_path


def main() -> None:
    _ensure_output_directories()

    print("Running ideal shot-sensitivity Monte Carlo study...")
    raw_rows = run_shot_sensitivity(
        sample_counts=SAMPLE_COUNTS,
        shot_counts=SHOT_COUNTS,
        seeds=SEEDS,
    )
    summary_rows = aggregate_shot_sensitivity_rows(raw_rows)

    print("Running representative Qiskit validation cases...")
    qiskit_validation = [
        validate_qiskit_shot_case(
            num_samples=num_samples,
            amplitude_bits=AMPLITUDE_BITS,
            shots=shots,
            seed=42,
        )
        for num_samples, shots in QISKIT_VALIDATION_CASES
    ]

    threshold_rows = _threshold_rows()

    generated_paths = [
        _write_csv(
            raw_rows,
            filename="shot_sensitivity_runs.csv",
        ),
        _write_csv(
            summary_rows,
            filename="shot_sensitivity_summary.csv",
        ),
        _write_json(
            raw_rows,
            summary_rows,
            qiskit_validation,
            threshold_rows,
        ),
        _write_markdown(
            summary_rows,
            qiskit_validation,
            threshold_rows,
        ),
        _plot_exact_reconstruction(summary_rows),
        _plot_coverage(summary_rows),
        _plot_missing_indices(summary_rows),
        _plot_tvd(summary_rows),
    ]

    print("Generated shot-sensitivity assets:")
    for path in generated_paths:
        print(f"  - {path}")

    print(f"Raw Monte Carlo runs: {len(raw_rows)}")
    print(f"Aggregated rows: {len(summary_rows)}")
    print(f"Qiskit validation cases: {len(qiskit_validation)}")

    for row in threshold_rows:
        print(
            f"N={row['num_samples']}:",
            f"95% threshold={row['shots_for_95_percent_full_coverage']},",
            f"99% threshold={row['shots_for_99_percent_full_coverage']}",
        )


if __name__ == "__main__":
    main()
