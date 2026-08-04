# Generating the First Reproducible Audio Experiment

This experiment creates the first visual and machine-readable evidence for the
basis-encoded quantum audio implementation.

## Install the visualization dependency

From the repository root:

```bash
pip install -e ".[notebook]"
```

## Run the experiment

```bash
python examples/audio/generate_basis_audio_assets.py
```

## Generated outputs

```text
figures/audio/basis_encoded_audio/
├── circuit.png
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

All generated results are tied to the script and fixed configuration so the
experiment can be reproduced.
