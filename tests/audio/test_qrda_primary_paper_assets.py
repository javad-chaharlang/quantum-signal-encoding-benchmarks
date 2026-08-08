"""Tests for QRDA primary-paper visual-asset generation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module():
    script_path = Path("examples/audio/generate_qrda_primary_paper_assets.py")
    spec = importlib.util.spec_from_file_location("qrda_primary_paper_assets", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load QRDA visual-assets script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_paper_example_metrics() -> None:
    module = _load_module()
    data = module.build_paper_example()
    spec = data["spec"]
    probabilities = data["probabilities"]

    assert spec.num_samples == 15
    assert spec.amplitude_bits == 4
    assert spec.time_bits == 4
    assert spec.total_qubits == 8
    assert spec.box_size == 16
    assert spec.padding_count == 1
    assert len(probabilities) == 16
    assert tuple(data["unsigned"]) == module.PAPER_UNSIGNED_SAMPLES
    assert tuple(data["reconstructed_unsigned"]) == module.PAPER_UNSIGNED_SAMPLES
    assert tuple(data["reconstructed_signed"]) == module.PAPER_SIGNED_SAMPLES


def test_generate_assets_smoke_without_rendering(tmp_path: Path) -> None:
    module = _load_module()

    figure_dir = tmp_path / "figures"
    result_dir = tmp_path / "results"

    report = module.generate_assets(
        figure_dir=figure_dir,
        result_dir=result_dir,
        render_circuit_images=False,
        render_plots=False,
    )

    assets_report = result_dir / "assets_report.json"
    readme_path = result_dir / "README.md"

    assert assets_report.exists()
    assert readme_path.exists()
    assert report["core_metrics"]["controlled_writes"] == 33
    assert report["reconstruction"]["unsigned_exact"] is True
    assert report["reconstruction"]["signed_exact"] is True

    data = json.loads(assets_report.read_text(encoding="utf-8"))
    assert data["core_metrics"]["total_qubits"] == 8
    assert data["core_metrics"]["padding_count"] == 1
