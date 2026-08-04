"""Run controlled resource-scaling studies for basis-encoded quantum audio."""

from __future__ import annotations

import csv
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib.pyplot as plt

from qseb.benchmarks import (
    aggregate_resource_rows,
    benchmark_resource_case,
    run_amplitude_resolution_scaling,
    run_signal_length_scaling,
)

RANDOM_SEEDS = (42, 52, 62, 72, 82)
SEED_TRANSPILER = 42
OPTIMIZATION_LEVEL = 1
TIMING_REPEATS = 3
BASIS_GATES = ("rz", "sx", "x", "cx")
PROFILES = ("sparse", "random", "dense")

SIGNAL_LENGTHS = (2, 4, 8, 16, 32)
FIXED_AMPLITUDE_BITS = 4

AMPLITUDE_WIDTHS = (2, 3, 4, 5, 6, 7, 8)
FIXED_NUM_SAMPLES = 8

RESULT_DIR = Path("results/audio/resource_scaling")
FIGURE_DIR = Path("figures/audio/resource_scaling")


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


def _remove_legacy_outputs() -> None:
    """Remove exploratory files superseded by the controlled benchmark."""

    legacy_paths = (
        RESULT_DIR / "resource_scaling.csv",
        FIGURE_DIR / "amplitude_depth.png",
        FIGURE_DIR / "amplitude_size.png",
        FIGURE_DIR / "length_cx_count.png",
        FIGURE_DIR / "length_depth.png",
        FIGURE_DIR / "length_size.png",
    )

    for path in legacy_paths:
        if path.exists():
            path.unlink()


def _warm_up_transpiler() -> None:
    benchmark_resource_case(
        num_samples=2,
        amplitude_bits=2,
        profile="sparse",
        seed=RANDOM_SEEDS[0],
        optimization_level=OPTIMIZATION_LEVEL,
        basis_gates=BASIS_GATES,
        seed_transpiler=SEED_TRANSPILER,
        timing_repeats=1,
    )


def _serialize_csv_value(value: object) -> object:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value


def _write_rows_csv(rows: list[dict[str, object]]) -> Path:
    output_path = RESULT_DIR / "resource_scaling_runs.csv"
    fieldnames = list(rows[0])

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _serialize_csv_value(value) for key, value in row.items()})

    return output_path


def _write_summary_csv(rows: list[dict[str, object]]) -> Path:
    output_path = RESULT_DIR / "resource_scaling_summary.csv"
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
        "benchmark": "controlled_basis_encoded_quantum_audio_resource_scaling",
        "environment": _environment_metadata(),
        "configuration": {
            "random_seeds": list(RANDOM_SEEDS),
            "seed_transpiler": SEED_TRANSPILER,
            "optimization_level": OPTIMIZATION_LEVEL,
            "timing_repeats": TIMING_REPEATS,
            "basis_gates": list(BASIS_GATES),
            "profiles": {
                "sparse": "one set amplitude bit per sample",
                "random": "uniform random amplitudes aggregated across five seeds",
                "dense": "all amplitude bits set for every sample",
            },
            "signal_length_study": {
                "sample_counts": list(SIGNAL_LENGTHS),
                "fixed_amplitude_bits": FIXED_AMPLITUDE_BITS,
            },
            "amplitude_resolution_study": {
                "amplitude_widths": list(AMPLITUDE_WIDTHS),
                "fixed_num_samples": FIXED_NUM_SAMPLES,
            },
            "barriers_enabled": False,
            "simulation_performed": False,
        },
        "raw_runs": raw_rows,
        "summary": summary_rows,
    }

    output_path = RESULT_DIR / "resource_scaling.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _study_rows(
    summary_rows: list[dict[str, object]],
    study: str,
) -> list[dict[str, object]]:
    return [row for row in summary_rows if row["study"] == study]


def _plot_profile_metric(
    *,
    rows: list[dict[str, object]],
    x_key: str,
    x_label: str,
    metric: str,
    y_label: str,
    title: str,
    filename: str,
    logarithmic_y: bool = False,
) -> Path:
    figure, axis = plt.subplots(figsize=(9.2, 5.4))

    markers = {
        "sparse": "^",
        "random": "o",
        "dense": "s",
    }

    for profile in PROFILES:
        profile_rows = sorted(
            (row for row in rows if row["profile"] == profile),
            key=lambda row: int(row[x_key]),
        )
        x_values = [int(row[x_key]) for row in profile_rows]
        means = [float(row[f"{metric}_mean"]) for row in profile_rows]
        standard_deviations = [float(row[f"{metric}_std"]) for row in profile_rows]

        if profile == "random":
            axis.errorbar(
                x_values,
                means,
                yerr=standard_deviations,
                marker=markers[profile],
                capsize=4,
                label="Random: mean ± SD",
            )
        else:
            axis.plot(
                x_values,
                means,
                marker=markers[profile],
                label=profile.capitalize(),
            )

    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.set_title(title)
    axis.set_xticks(sorted({int(row[x_key]) for row in rows}))
    if logarithmic_y:
        axis.set_yscale("log")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    output_path = FIGURE_DIR / filename
    figure.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _format_mean_std(row: dict[str, object], metric: str) -> str:
    metric_mean = float(row[f"{metric}_mean"])
    metric_std = float(row[f"{metric}_std"])

    if int(row["runs"]) > 1:
        return f"{metric_mean:.1f} ± {metric_std:.1f}"

    return f"{metric_mean:.1f}"


def _markdown_table(
    rows: list[dict[str, object]],
    *,
    x_key: str,
    x_heading: str,
) -> str:
    lines = [
        (
            f"| {x_heading} | Profile | Runs | Qubits | Hamming weight | "
            "Transpiled depth | Transpiled size | CX count | Depth overhead |"
        ),
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in sorted(
        rows,
        key=lambda item: (int(item[x_key]), PROFILES.index(str(item["profile"]))),
    ):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row[x_key]),
                    str(row["profile"]),
                    str(row["runs"]),
                    str(row["total_qubits"]),
                    _format_mean_std(row, "sample_hamming_weight"),
                    _format_mean_std(row, "transpiled_depth"),
                    _format_mean_std(row, "transpiled_size"),
                    _format_mean_std(row, "transpiled_cx_count"),
                    _format_mean_std(row, "depth_overhead_ratio"),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _summary_row(
    rows: list[dict[str, object]],
    *,
    study: str,
    profile: str,
    x_key: str,
    x_value: int,
) -> dict[str, object]:
    for row in rows:
        if row["study"] == study and row["profile"] == profile and int(row[x_key]) == x_value:
            return row

    raise ValueError(f"missing summary row: study={study}, profile={profile}, {x_key}={x_value}")


def _write_markdown(summary_rows: list[dict[str, object]]) -> Path:
    length_rows = _study_rows(summary_rows, "signal_length")
    amplitude_rows = _study_rows(summary_rows, "amplitude_resolution")

    length_table = _markdown_table(
        length_rows,
        x_key="num_samples",
        x_heading="Samples",
    )
    amplitude_table = _markdown_table(
        amplitude_rows,
        x_key="amplitude_bits",
        x_heading="Amplitude bits",
    )

    random_length_start = _summary_row(
        summary_rows,
        study="signal_length",
        profile="random",
        x_key="num_samples",
        x_value=min(SIGNAL_LENGTHS),
    )
    random_length_end = _summary_row(
        summary_rows,
        study="signal_length",
        profile="random",
        x_key="num_samples",
        x_value=max(SIGNAL_LENGTHS),
    )
    dense_amplitude_start = _summary_row(
        summary_rows,
        study="amplitude_resolution",
        profile="dense",
        x_key="amplitude_bits",
        x_value=min(AMPLITUDE_WIDTHS),
    )
    dense_amplitude_end = _summary_row(
        summary_rows,
        study="amplitude_resolution",
        profile="dense",
        x_key="amplitude_bits",
        x_value=max(AMPLITUDE_WIDTHS),
    )
    sparse_amplitude_start = _summary_row(
        summary_rows,
        study="amplitude_resolution",
        profile="sparse",
        x_key="amplitude_bits",
        x_value=min(AMPLITUDE_WIDTHS),
    )
    sparse_amplitude_end = _summary_row(
        summary_rows,
        study="amplitude_resolution",
        profile="sparse",
        x_key="amplitude_bits",
        x_value=max(AMPLITUDE_WIDTHS),
    )

    random_depth_growth = float(random_length_end["transpiled_depth_mean"]) / float(
        random_length_start["transpiled_depth_mean"]
    )
    random_cx_growth = float(random_length_end["transpiled_cx_count_mean"]) / float(
        random_length_start["transpiled_cx_count_mean"]
    )
    dense_depth_per_bit = (
        float(dense_amplitude_end["transpiled_depth_mean"])
        - float(dense_amplitude_start["transpiled_depth_mean"])
    ) / (max(AMPLITUDE_WIDTHS) - min(AMPLITUDE_WIDTHS))
    dense_cx_per_bit = (
        float(dense_amplitude_end["transpiled_cx_count_mean"])
        - float(dense_amplitude_start["transpiled_cx_count_mean"])
    ) / (max(AMPLITUDE_WIDTHS) - min(AMPLITUDE_WIDTHS))
    sparse_depth_change = 100.0 * (
        float(sparse_amplitude_end["transpiled_depth_mean"])
        / float(sparse_amplitude_start["transpiled_depth_mean"])
        - 1.0
    )

    summary = f"""# Controlled Resource Scaling: Basis-Encoded Quantum Audio

## Purpose

This benchmark measures how the current explicit state-preparation circuit scales
with signal length, amplitude-register width, and amplitude-bit density.

## Controlled design

Three input profiles are evaluated:

- **Sparse:** one set amplitude bit per sample.
- **Random:** uniform random amplitudes aggregated across five fixed seeds.
- **Dense:** all amplitude bits set for every sample.

Configuration:

- Random seeds: `{list(RANDOM_SEEDS)}`
- Transpiler seed: `{SEED_TRANSPILER}`
- Optimization level: `{OPTIMIZATION_LEVEL}`
- Timing repeats: `{TIMING_REPEATS}`; the median is reported per run
- Basis gates: `{list(BASIS_GATES)}`
- Barriers disabled during resource measurement
- No statevector, shot-based, noisy, or hardware execution

## Key findings from this run

1. **Signal length is the dominant scaling pressure.** For the random profile,
   increasing the signal from `{min(SIGNAL_LENGTHS)}` to `{max(SIGNAL_LENGTHS)}`
   samples increased mean transpiled depth by `{random_depth_growth:.1f}x` and
   mean CX count by `{random_cx_growth:.1f}x`, while total qubits increased only
   from `{random_length_start["total_qubits"]}` to
   `{random_length_end["total_qubits"]}`.
2. **Transpilation overhead becomes dominant at longer signals.** At
   `{max(SIGNAL_LENGTHS)}` samples, the random profile reached a mean depth
   overhead of `{float(random_length_end["depth_overhead_ratio_mean"]):.1f}x`.
3. **Amplitude width alone is not the full cost driver.** Under the dense
   profile, each additional amplitude qubit added exactly
   `{dense_depth_per_bit:.0f}` layers of transpiled depth and
   `{dense_cx_per_bit:.0f}` CX gates across the tested range.
4. **Fixed loading sparsity keeps cost nearly constant.** The sparse
   amplitude-resolution profile held the number of loaded amplitude bits fixed,
   and transpiled depth changed by only `{sparse_depth_change:.1f}%` from
   `{min(AMPLITUDE_WIDTHS)}` to `{max(AMPLITUDE_WIDTHS)}` amplitude qubits.

The central conclusion is that state-preparation cost is jointly controlled by
the width of the time-register controls and the number of set amplitude bits.
Qubit count alone is therefore not a sufficient resource indicator.

## Study A: signal-length scaling

{length_table}

![Transpiled depth versus signal length][length-depth]

![CX count versus signal length][length-cx]

![Depth overhead versus signal length][length-overhead]

## Study B: amplitude-resolution scaling

{amplitude_table}

![Transpiled depth versus amplitude width][amplitude-depth]

![CX count versus amplitude width][amplitude-cx]

![Depth overhead versus amplitude width][amplitude-overhead]

## Interpretation boundary

The sparse and dense profiles expose lower- and upper-content-loading regimes, while
the random profile estimates typical variability. This prevents amplitude-register
width from being confused with a single signal's number of set bits.

These measurements characterize the present circuit construction and selected
transpiler configuration. They do not establish quantum advantage, hardware
feasibility, execution fidelity, or asymptotic optimality.

Machine-readable outputs:

- `results/audio/resource_scaling/resource_scaling_runs.csv`
- `results/audio/resource_scaling/resource_scaling_summary.csv`
- `results/audio/resource_scaling/resource_scaling.json`

[length-depth]: ../../../figures/audio/resource_scaling/length_transpiled_depth_profiles.png
[length-cx]: ../../../figures/audio/resource_scaling/length_transpiled_cx_profiles.png
[length-overhead]: ../../../figures/audio/resource_scaling/length_depth_overhead_profiles.png
[amplitude-depth]: ../../../figures/audio/resource_scaling/amplitude_transpiled_depth_profiles.png
[amplitude-cx]: ../../../figures/audio/resource_scaling/amplitude_transpiled_cx_profiles.png
[amplitude-overhead]: ../../../figures/audio/resource_scaling/amplitude_depth_overhead_profiles.png
"""

    output_path = RESULT_DIR / "README.md"
    output_path.write_text(summary, encoding="utf-8")
    return output_path


def main() -> None:
    _ensure_output_directories()
    _remove_legacy_outputs()

    print("Warming up the transpiler...")
    _warm_up_transpiler()

    print("Running controlled signal-length scaling study...")
    length_rows = run_signal_length_scaling(
        SIGNAL_LENGTHS,
        amplitude_bits=FIXED_AMPLITUDE_BITS,
        profiles=PROFILES,
        random_seeds=RANDOM_SEEDS,
        optimization_level=OPTIMIZATION_LEVEL,
        basis_gates=BASIS_GATES,
        seed_transpiler=SEED_TRANSPILER,
        timing_repeats=TIMING_REPEATS,
    )

    print("Running controlled amplitude-resolution scaling study...")
    amplitude_rows = run_amplitude_resolution_scaling(
        AMPLITUDE_WIDTHS,
        num_samples=FIXED_NUM_SAMPLES,
        profiles=PROFILES,
        random_seeds=RANDOM_SEEDS,
        optimization_level=OPTIMIZATION_LEVEL,
        basis_gates=BASIS_GATES,
        seed_transpiler=SEED_TRANSPILER,
        timing_repeats=TIMING_REPEATS,
    )

    raw_rows = [*length_rows, *amplitude_rows]
    summary_rows = aggregate_resource_rows(raw_rows)

    length_summary = _study_rows(summary_rows, "signal_length")
    amplitude_summary = _study_rows(summary_rows, "amplitude_resolution")

    generated_paths = [
        _write_rows_csv(raw_rows),
        _write_summary_csv(summary_rows),
        _write_json(raw_rows, summary_rows),
        _write_markdown(summary_rows),
        _plot_profile_metric(
            rows=length_summary,
            x_key="num_samples",
            x_label="Number of samples",
            metric="transpiled_depth",
            y_label="Transpiled circuit depth",
            title="Transpiled Depth versus Signal Length",
            filename="length_transpiled_depth_profiles.png",
            logarithmic_y=True,
        ),
        _plot_profile_metric(
            rows=length_summary,
            x_key="num_samples",
            x_label="Number of samples",
            metric="transpiled_cx_count",
            y_label="CX gate count",
            title="Transpiled CX Count versus Signal Length",
            filename="length_transpiled_cx_profiles.png",
            logarithmic_y=True,
        ),
        _plot_profile_metric(
            rows=length_summary,
            x_key="num_samples",
            x_label="Number of samples",
            metric="depth_overhead_ratio",
            y_label="Transpiled depth / raw depth",
            title="Transpilation Depth Overhead versus Signal Length",
            filename="length_depth_overhead_profiles.png",
        ),
        _plot_profile_metric(
            rows=amplitude_summary,
            x_key="amplitude_bits",
            x_label="Amplitude-register width (qubits)",
            metric="transpiled_depth",
            y_label="Transpiled circuit depth",
            title="Transpiled Depth versus Amplitude Resolution",
            filename="amplitude_transpiled_depth_profiles.png",
        ),
        _plot_profile_metric(
            rows=amplitude_summary,
            x_key="amplitude_bits",
            x_label="Amplitude-register width (qubits)",
            metric="transpiled_cx_count",
            y_label="CX gate count",
            title="Transpiled CX Count versus Amplitude Resolution",
            filename="amplitude_transpiled_cx_profiles.png",
        ),
        _plot_profile_metric(
            rows=amplitude_summary,
            x_key="amplitude_bits",
            x_label="Amplitude-register width (qubits)",
            metric="depth_overhead_ratio",
            y_label="Transpiled depth / raw depth",
            title="Transpilation Depth Overhead versus Amplitude Resolution",
            filename="amplitude_depth_overhead_profiles.png",
        ),
    ]

    print("Generated controlled resource-scaling assets:")
    for path in generated_paths:
        print(f"  - {path}")

    print(f"Raw benchmark runs: {len(raw_rows)}")
    print(f"Aggregated benchmark rows: {len(summary_rows)}")


if __name__ == "__main__":
    main()
