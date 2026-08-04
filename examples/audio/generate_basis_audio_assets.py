"""Generate reproducible figures and reports for basis-encoded quantum audio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from qiskit.visualization import circuit_drawer

from qseb.audio import (
    build_basis_encoded_audio_circuit,
    circuit_resource_metrics,
    exact_basis_probabilities,
    reconstruct_from_counts,
    simulate_counts,
)

SAMPLES = [3, 6, 2, 5]
AMPLITUDE_BITS = 3
SHOTS = 4096
SEED = 42
OPTIMIZATION_LEVEL = 1

FIGURE_DIR = Path("figures/audio/basis_encoded_audio")
RESULT_DIR = Path("results/audio/basis_encoded_audio")

CIRCUIT_STYLE = {
    "name": "iqp",
    "backgroundcolor": "#FFFFFF",
    "textcolor": "#111827",
    "subtextcolor": "#374151",
    "linecolor": "#1F2937",
    "creglinecolor": "#64748B",
    "gatetextcolor": "#FFFFFF",
    "gatefacecolor": "#7C3AED",
    "barrierfacecolor": "#CBD5E1",
    "fontsize": 13,
    "subfontsize": 9,
    "displaycolor": {
        "h": ("#EF4444", "#FFFFFF"),
        "x": ("#2563EB", "#FFFFFF"),
        "cx": ("#2563EB", "#FFFFFF"),
        "ccx": ("#7C3AED", "#FFFFFF"),
        "mcx": ("#7C3AED", "#FFFFFF"),
        "barrier": ("#CBD5E1", "#334155"),
    },
}


def _ensure_output_directories() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def _remove_legacy_circuit_files() -> None:
    """Remove older black-and-white circuit files to prevent confusion."""

    for filename in ("circuit.png", "circuit.svg"):
        path = FIGURE_DIR / filename
        if path.exists():
            path.unlink()


def _save_circuit_figure(circuit: Any) -> tuple[Path, Path]:
    """Save publication-style Qiskit circuit figures as PNG and SVG."""

    png_output_path = FIGURE_DIR / "circuit_colored.png"
    svg_output_path = FIGURE_DIR / "circuit_colored.svg"

    figure = circuit_drawer(
        circuit,
        output="mpl",
        style=CIRCUIT_STYLE,
        fold=-1,
        scale=1.0,
        plot_barriers=True,
        idle_wires=False,
        vertical_compression="low",
    )

    if figure is None:
        raise RuntimeError("Qiskit did not return a Matplotlib circuit figure")

    figure.savefig(
        png_output_path,
        dpi=350,
        bbox_inches="tight",
        facecolor="white",
    )
    figure.savefig(
        svg_output_path,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)
    return png_output_path, svg_output_path


def _save_reconstruction_figure(
    original: list[int],
    reconstructed: list[int],
) -> Path:
    time_indices = list(range(len(original)))
    bar_width = 0.36

    figure, axis = plt.subplots(figsize=(8.5, 4.8))
    axis.bar(
        [index - bar_width / 2 for index in time_indices],
        original,
        width=bar_width,
        label="Original",
    )
    axis.bar(
        [index + bar_width / 2 for index in time_indices],
        reconstructed,
        width=bar_width,
        label="Reconstructed",
    )

    axis.set_xlabel("Time index")
    axis.set_ylabel("Quantized amplitude")
    axis.set_title("Basis-Encoded Quantum Audio Reconstruction")
    axis.set_xticks(time_indices)
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()

    output_path = FIGURE_DIR / "reconstruction.png"
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _save_counts_figure(counts: dict[str, int]) -> Path:
    ordered_items = sorted(counts.items(), key=lambda item: item[0])
    states = [state for state, _ in ordered_items]
    frequencies = [frequency for _, frequency in ordered_items]

    figure, axis = plt.subplots(figsize=(9.5, 4.8))
    axis.bar(states, frequencies)
    axis.set_xlabel("Measured computational-basis state")
    axis.set_ylabel("Counts")
    axis.set_title(f"Measurement Distribution ({SHOTS} shots, seed={SEED})")
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()

    output_path = FIGURE_DIR / "measurement_counts.png"
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _serializable_probabilities(
    probabilities: dict[tuple[int, int], float],
) -> list[dict[str, float | int]]:
    return [
        {
            "time_index": time_index,
            "amplitude": amplitude,
            "probability": probability,
        }
        for (time_index, amplitude), probability in sorted(probabilities.items())
    ]


def _write_json_report(
    *,
    spec: Any,
    reconstructed: list[int],
    counts: dict[str, int],
    probabilities: dict[tuple[int, int], float],
    resources: dict[str, object],
) -> Path:
    report = {
        "experiment": "basis_encoded_quantum_audio",
        "input_samples": SAMPLES,
        "reconstructed_samples": reconstructed,
        "exact_reconstruction": reconstructed == SAMPLES,
        "amplitude_bits": spec.amplitude_bits,
        "time_bits": spec.time_bits,
        "total_qubits": spec.total_qubits,
        "shots": SHOTS,
        "seed_simulator": SEED,
        "optimization_level": OPTIMIZATION_LEVEL,
        "exact_basis_probabilities": _serializable_probabilities(probabilities),
        "measurement_counts": dict(sorted(counts.items())),
        "resource_metrics": resources,
        "figure_files": {
            "circuit_png": "figures/audio/basis_encoded_audio/circuit_colored.png",
            "circuit_svg": "figures/audio/basis_encoded_audio/circuit_colored.svg",
            "reconstruction": "figures/audio/basis_encoded_audio/reconstruction.png",
            "measurement_counts": (
                "figures/audio/basis_encoded_audio/measurement_counts.png"
            ),
        },
    }

    output_path = RESULT_DIR / "experiment_report.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _write_markdown_summary(
    *,
    spec: Any,
    reconstructed: list[int],
    resources: dict[str, object],
) -> Path:
    summary = f"""# Basis-Encoded Quantum Audio: Reproducible Experiment

## Configuration

| Item | Value |
|---|---:|
| Input samples | `{SAMPLES}` |
| Amplitude qubits | {spec.amplitude_bits} |
| Time qubits | {spec.time_bits} |
| Total qubits | {spec.total_qubits} |
| Shots | {SHOTS} |
| Simulator seed | {SEED} |
| Transpiler optimization level | {OPTIMIZATION_LEVEL} |

## Reconstruction

- Original: `{SAMPLES}`
- Reconstructed: `{reconstructed}`
- Exact reconstruction: **{reconstructed == SAMPLES}**

![Original and reconstructed samples](../../../figures/audio/basis_encoded_audio/reconstruction.png)

## Colored Qiskit circuit

![Colored basis-encoded audio circuit](../../../figures/audio/basis_encoded_audio/circuit_colored.png)

A scalable vector version is available at
`figures/audio/basis_encoded_audio/circuit_colored.svg`.

## Measurement distribution

![Measurement counts](../../../figures/audio/basis_encoded_audio/measurement_counts.png)

## Resource metrics

| Metric | Value |
|---|---:|
| Raw depth | {resources["raw_depth"]} |
| Raw size | {resources["raw_size"]} |
| Transpiled depth | {resources["transpiled_depth"]} |
| Transpiled size | {resources["transpiled_size"]} |

The complete machine-readable report is available in
`results/audio/basis_encoded_audio/experiment_report.json`.

## Interpretation

This experiment verifies that the small unsigned integer signal is encoded into
time-indexed computational-basis amplitudes and reconstructed exactly under ideal
shot-based simulation. It is a transparent baseline rather than a claim of quantum
advantage. The next benchmark should study scaling, finite-shot coverage, and noise.
"""

    output_path = RESULT_DIR / "README.md"
    output_path.write_text(summary, encoding="utf-8")
    return output_path


def main() -> None:
    _ensure_output_directories()
    _remove_legacy_circuit_files()

    circuit, spec = build_basis_encoded_audio_circuit(
        SAMPLES,
        amplitude_bits=AMPLITUDE_BITS,
    )
    probabilities = exact_basis_probabilities(circuit, spec)
    counts = simulate_counts(
        circuit,
        shots=SHOTS,
        seed_simulator=SEED,
        optimization_level=OPTIMIZATION_LEVEL,
    )
    reconstructed = reconstruct_from_counts(counts, spec)
    resources = circuit_resource_metrics(
        circuit,
        optimization_level=OPTIMIZATION_LEVEL,
    )

    circuit_png_path, circuit_svg_path = _save_circuit_figure(circuit)

    generated_paths = [
        circuit_png_path,
        circuit_svg_path,
        _save_reconstruction_figure(SAMPLES, reconstructed),
        _save_counts_figure(counts),
        _write_json_report(
            spec=spec,
            reconstructed=reconstructed,
            counts=counts,
            probabilities=probabilities,
            resources=resources,
        ),
        _write_markdown_summary(
            spec=spec,
            reconstructed=reconstructed,
            resources=resources,
        ),
    ]

    print("Generated reproducible assets:")
    for path in generated_paths:
        print(f"  - {path}")

    print(f"Exact reconstruction: {reconstructed == SAMPLES}")


if __name__ == "__main__":
    main()
