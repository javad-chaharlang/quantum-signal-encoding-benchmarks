# Generating the First Reproducible Audio Experiment

This experiment creates visual and machine-readable evidence for the
basis-encoded quantum audio implementation.

## Install the project and visualization dependencies

From the repository root:

```bash
pip install -e ".[dev,notebook]"
```

The `notebook` extra installs Matplotlib and `pylatexenc`, which are required by
the Qiskit Matplotlib circuit drawer.

## Run the experiment

```bash
python examples/audio/generate_basis_audio_assets.py
```

## Generated outputs

```text
figures/audio/basis_encoded_audio/
├── circuit_colored.png
├── circuit_colored.svg
├── measurement_counts.png
└── reconstruction.png

results/audio/basis_encoded_audio/
├── experiment_report.json
└── README.md
```

The run uses:

- Input signal: `[3, 6, 2, 5]`
- Amplitude bits: `3`
- Shots: `4096`
- Simulator seed: `42`
- Transpiler optimization level: `1`

The PNG circuit is intended for GitHub and LinkedIn. The SVG circuit is intended
for high-resolution viewing, publication figures, and later editing.

All generated results are tied to the script and fixed configuration so the
experiment can be reproduced.
