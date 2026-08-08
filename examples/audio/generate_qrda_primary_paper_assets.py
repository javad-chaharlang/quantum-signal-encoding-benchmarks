"""Generate visual assets for the primary QRDA paper example.

This script adds a visual layer on top of the existing QRDA primary-paper
reproduction and protocol-validation workflow.

Outputs
-------
Figures:
    figures/audio/qrda_primary_paper/
        qrda_logical_circuit.png
        qrda_logical_circuit.svg
        qrda_transpiled_o0.png
        qrda_transpiled_o0.svg
        qrda_transpiled_o1.png
        qrda_transpiled_o1.svg
        signed_unsigned_signal.png
        state_support.png
        reconstruction_unsigned.png
        reconstruction_signed.png
        protocol_comparison.png

Results:
    results/audio/qrda_primary_paper/
        assets_report.json
        README.md

Notes
-----
- Circuit and plot rendering use Matplotlib and Qiskit's Matplotlib drawer.
  These dependencies are imported only when rendering is requested. Install with:

      python -m pip install -e ".[dev,notebook]"

- The script does not change the scientific QRDA core. It only produces
  visual outputs and a compact machine-readable report.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from qiskit import transpile

from qseb.audio import (
    build_qrda_circuit,
    exact_qrda_probabilities,
    reconstruct_qrda_signal,
    signed_to_unsigned_samples,
    simulate_qrda_counts,
    unsigned_to_signed_samples,
)

PAPER_SIGNED_SAMPLES = (
    0,
    3,
    5,
    7,
    7,
    5,
    3,
    0,
    -3,
    -5,
    -7,
    -7,
    -5,
    -3,
    0,
)

PAPER_UNSIGNED_SAMPLES = (
    8,
    11,
    13,
    15,
    15,
    13,
    11,
    8,
    5,
    3,
    1,
    1,
    3,
    5,
    8,
)

AMPLITUDE_BITS = 4
SHOTS = 16384
SEED_SIMULATOR = 42
BASIS_GATES = ["rz", "sx", "x", "cx"]

FIGURE_DIR = Path("figures/audio/qrda_primary_paper")
RESULT_DIR = Path("results/audio/qrda_primary_paper")


def _get_pyplot():
    """Import Matplotlib only when visual rendering is requested."""
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "QRDA visual rendering requires Matplotlib. "
            "Install the visual dependencies with: "
            'python -m pip install -e ".[dev,notebook]"'
        ) from exc

    return plt


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_paper_example():
    """Return the logical QRDA circuit, spec, probabilities, and reconstructions."""
    unsigned = signed_to_unsigned_samples(
        PAPER_SIGNED_SAMPLES,
        amplitude_bits=AMPLITUDE_BITS,
    )
    circuit, spec = build_qrda_circuit(unsigned, amplitude_bits=AMPLITUDE_BITS)
    probabilities = exact_qrda_probabilities(circuit, spec)

    counts = simulate_qrda_counts(
        circuit,
        shots=SHOTS,
        seed_simulator=SEED_SIMULATOR,
    )
    reconstructed_unsigned = tuple(reconstruct_qrda_signal(counts, spec))
    reconstructed_signed = unsigned_to_signed_samples(
        reconstructed_unsigned,
        amplitude_bits=AMPLITUDE_BITS,
    )

    return {
        "unsigned": unsigned,
        "circuit": circuit,
        "spec": spec,
        "probabilities": probabilities,
        "counts": counts,
        "reconstructed_unsigned": reconstructed_unsigned,
        "reconstructed_signed": reconstructed_signed,
    }


def _save_circuit_images(circuit, stem: str, out_dir: Path) -> dict[str, str]:
    """Save a Qiskit circuit in PNG and SVG formats."""
    plt = _get_pyplot()

    figure = circuit.draw(output="mpl", fold=-1)
    png_path = out_dir / f"{stem}.png"
    svg_path = out_dir / f"{stem}.svg"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight")
    plt.close(figure)
    return {
        "png": str(png_path),
        "svg": str(svg_path),
    }


def _plot_signed_unsigned_signal(out_dir: Path) -> str:
    plt = _get_pyplot()

    plt.figure(figsize=(10, 5))
    x = list(range(len(PAPER_SIGNED_SAMPLES)))
    plt.plot(x, PAPER_SIGNED_SAMPLES, marker="o", label="Signed signal")
    plt.plot(x, PAPER_UNSIGNED_SAMPLES, marker="o", label="Unsigned QRDA amplitudes")
    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.title("Primary-paper signal: signed to unsigned QRDA translation")
    plt.legend()
    plt.tight_layout()

    output_path = out_dir / "signed_unsigned_signal.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    return str(output_path)


def _plot_state_support(
    probabilities: Mapping[tuple[int, int], float],
    out_dir: Path,
) -> str:
    plt = _get_pyplot()

    states = sorted(probabilities.items())
    labels = [f"({time_index},{amplitude})" for (time_index, amplitude), _ in states]
    values = [probability for _, probability in states]

    plt.figure(figsize=(12, 5))
    plt.bar(range(len(labels)), values)
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.xlabel("(time_index, amplitude)")
    plt.ylabel("Probability")
    plt.title("Exact QRDA support of the primary-paper state")
    plt.tight_layout()

    output_path = out_dir / "state_support.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    return str(output_path)


def _plot_reconstruction(
    original: tuple[int, ...] | list[int],
    reconstructed: tuple[int, ...] | list[int],
    title: str,
    filename: str,
    out_dir: Path,
) -> str:
    plt = _get_pyplot()

    x = list(range(len(original)))

    plt.figure(figsize=(10, 5))
    plt.plot(x, original, marker="o", label="Original")
    plt.plot(x, reconstructed, marker="o", linestyle="--", label="Reconstructed")
    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.title(title)
    plt.legend()
    plt.tight_layout()

    output_path = out_dir / filename
    plt.savefig(output_path, dpi=300)
    plt.close()
    return str(output_path)


def _plot_protocol_comparison(circuit, out_dir: Path) -> str:
    plt = _get_pyplot()

    ops = circuit.count_ops()
    labels = [
        "Paper H",
        "Qiskit H",
        "Paper writes",
        "Qiskit MCX",
        "X wrappers",
    ]
    values = [
        4,
        ops.get("h", 0),
        33,
        ops.get("mcx", 0),
        ops.get("x", 0),
    ]

    plt.figure(figsize=(10, 5))
    plt.bar(range(len(labels)), values)
    plt.xticks(range(len(labels)), labels, rotation=20, ha="right")
    plt.ylabel("Count")
    plt.title("Primary-paper protocol vs QRDA Qiskit implementation")
    plt.tight_layout()

    output_path = out_dir / "protocol_comparison.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    return str(output_path)


def _write_results_readme(figure_dir: Path, result_dir: Path, report: dict[str, object]) -> str:
    relative = "../../../figures/audio/qrda_primary_paper"

    lines = [
        "# QRDA primary-paper visual assets",
        "",
        "This folder contains the visual outputs generated by",
        "`examples/audio/generate_qrda_primary_paper_assets.py`.",
        "",
        "## Summary",
        "",
        f"- Total qubits: {report['core_metrics']['total_qubits']}",
        f"- QRDA box size: {report['core_metrics']['box_size']}",
        f"- Padding count: {report['core_metrics']['padding_count']}",
        f"- Controlled writes: {report['core_metrics']['controlled_writes']}",
        f"- Exact unsigned reconstruction: {report['reconstruction']['unsigned_exact']}",
        f"- Exact signed reconstruction: {report['reconstruction']['signed_exact']}",
        "",
        "## Figures",
        "",
        f"### Logical QRDA circuit",
        f"![logical circuit]({relative}/qrda_logical_circuit.png)",
        "",
        f"### Transpiled circuit (optimization level 0)",
        f"![transpiled o0]({relative}/qrda_transpiled_o0.png)",
        "",
        f"### Transpiled circuit (optimization level 1)",
        f"![transpiled o1]({relative}/qrda_transpiled_o1.png)",
        "",
        f"### Signed to unsigned translation",
        f"![signed unsigned]({relative}/signed_unsigned_signal.png)",
        "",
        f"### Exact state support",
        f"![state support]({relative}/state_support.png)",
        "",
        f"### Unsigned reconstruction",
        f"![unsigned reconstruction]({relative}/reconstruction_unsigned.png)",
        "",
        f"### Signed reconstruction",
        f"![signed reconstruction]({relative}/reconstruction_signed.png)",
        "",
        f"### Protocol comparison",
        f"![protocol comparison]({relative}/protocol_comparison.png)",
        "",
        "## Machine-readable report",
        "",
        "- `assets_report.json`",
    ]

    output_path = result_dir / "README.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output_path)


def generate_assets(
    *,
    figure_dir: Path | str = FIGURE_DIR,
    result_dir: Path | str = RESULT_DIR,
    render_circuit_images: bool = True,
    render_plots: bool = True,
) -> dict[str, object]:
    """Generate visual QRDA assets and return a summary report."""
    figure_dir = _ensure_dir(Path(figure_dir))
    result_dir = _ensure_dir(Path(result_dir))

    data = build_paper_example()
    circuit = data["circuit"]
    spec = data["spec"]
    probabilities = data["probabilities"]
    reconstructed_unsigned = data["reconstructed_unsigned"]
    reconstructed_signed = data["reconstructed_signed"]

    figures: dict[str, object] = {}

    if render_circuit_images:
        figures["qrda_logical_circuit"] = _save_circuit_images(
            circuit,
            "qrda_logical_circuit",
            figure_dir,
        )

        transpiled_o0 = transpile(
            circuit,
            basis_gates=BASIS_GATES,
            optimization_level=0,
            seed_transpiler=42,
        )
        figures["qrda_transpiled_o0"] = _save_circuit_images(
            transpiled_o0,
            "qrda_transpiled_o0",
            figure_dir,
        )

        transpiled_o1 = transpile(
            circuit,
            basis_gates=BASIS_GATES,
            optimization_level=1,
            seed_transpiler=42,
        )
        figures["qrda_transpiled_o1"] = _save_circuit_images(
            transpiled_o1,
            "qrda_transpiled_o1",
            figure_dir,
        )

    if render_plots:
        figures["signed_unsigned_signal"] = _plot_signed_unsigned_signal(figure_dir)
        figures["state_support"] = _plot_state_support(probabilities, figure_dir)
        figures["reconstruction_unsigned"] = _plot_reconstruction(
            PAPER_UNSIGNED_SAMPLES,
            reconstructed_unsigned,
            "Unsigned QRDA amplitudes: original vs reconstructed",
            "reconstruction_unsigned.png",
            figure_dir,
        )
        figures["reconstruction_signed"] = _plot_reconstruction(
            PAPER_SIGNED_SAMPLES,
            reconstructed_signed,
            "Signed signal: original vs reconstructed",
            "reconstruction_signed.png",
            figure_dir,
        )
        figures["protocol_comparison"] = _plot_protocol_comparison(circuit, figure_dir)

    report = {
        "reference": {
            "title": "QRDA: Quantum Representation of Digital Audio",
            "author": "Jian Wang",
            "year": 2016,
            "doi": "10.1007/s10773-015-2800-2",
        },
        "core_metrics": {
            "num_samples": spec.num_samples,
            "amplitude_bits": spec.amplitude_bits,
            "time_bits": spec.time_bits,
            "total_qubits": spec.total_qubits,
            "box_size": spec.box_size,
            "padding_count": spec.padding_count,
            "padding_fraction": spec.padding_fraction,
            "controlled_writes": int(sum(value.bit_count() for value in PAPER_UNSIGNED_SAMPLES)),
            "nonzero_support_states": len(probabilities),
        },
        "reconstruction": {
            "unsigned_exact": tuple(reconstructed_unsigned) == PAPER_UNSIGNED_SAMPLES,
            "signed_exact": tuple(reconstructed_signed) == PAPER_SIGNED_SAMPLES,
            "unsigned_reconstructed": list(reconstructed_unsigned),
            "signed_reconstructed": list(reconstructed_signed),
        },
        "figures": figures,
    }

    report_path = result_dir / "assets_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    readme_path = _write_results_readme(figure_dir, result_dir, report)

    report["results"] = {
        "assets_report": str(report_path),
        "results_readme": readme_path,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def main() -> None:
    report = generate_assets()
    print("Generated QRDA visual assets:")
    for key, value in report["figures"].items():
        if isinstance(value, dict):
            for filetype, path in value.items():
                print(f"  - {key} [{filetype}]: {path}")
        else:
            print(f"  - {key}: {value}")
    print(f"  - assets_report: {report['results']['assets_report']}")
    print(f"  - results_readme: {report['results']['results_readme']}")
    print()
    print("Core metrics:")
    for key, value in report["core_metrics"].items():
        print(f"  - {key}: {value}")
    print()
    print("Exact unsigned reconstruction:", report["reconstruction"]["unsigned_exact"])
    print("Exact signed reconstruction:  ", report["reconstruction"]["signed_exact"])


if __name__ == "__main__":
    main()
