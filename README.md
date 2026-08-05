# Quantum Signal Encoding Benchmarks

[![CI](https://github.com/javad-chaharlang/quantum-signal-encoding-benchmarks/actions/workflows/ci.yml/badge.svg)](https://github.com/javad-chaharlang/quantum-signal-encoding-benchmarks/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.4%2B-6929C4.svg)](https://www.ibm.com/quantum/qiskit)
[![License](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![Research Software](https://img.shields.io/badge/Research-Reproducible-informational.svg)](#reproducibility)

A reproducible research repository for implementing and benchmarking **quantum representations of classical signals** with Qiskit. The project begins with quantum audio and image encoding, then develops toward hybrid quantum-classical medical imaging and secure quantum multimedia processing.

> **Research principle:** an encoding method is not considered complete until its state definition, circuit preparation, decoding procedure, reconstruction accuracy, resource requirements, and noise sensitivity are documented.

## Current release: v0.2.0

Version 0.2 formalizes the existing unsigned amplitude/time encoder as a **QRDA state-representation implementation**:

```math
|A\rangle =
\frac{1}{\sqrt{N}}
\sum_{t=0}^{N-1}
|a_t\rangle_{\mathrm{amp}}
|t\rangle_{\mathrm{time}}.
```

where each quantized audio amplitude $a_t$ is stored in an amplitude register and each sample index $t$ is stored in a time register.

The state structure matches QRDA's entangled computational-basis amplitude and time registers. The implementation accepts unsigned quantized amplitudes; bipolar samples require a recorded offset before encoding. Exact reproduction of the primary paper's worked example and gate-level protocol remains an explicit validation item.

### Included

- QRDA-specific public API with backward-compatible legacy aliases
- Explicit documentation of unsigned amplitude encoding and bipolar offset mapping
- Validated integer audio quantization input
- Reversible Qiskit state-preparation circuit
- Exact statevector verification
- Shot-based Aer simulation
- Measurement decoding and signal reconstruction
- Circuit resource reporting
- Controlled resource-scaling benchmark
- Controlled shot-sensitivity benchmark with exact theoretical reference
- Controlled synthetic gate and readout noise benchmark
- Calibration-derived hardware-noise benchmark with layout analysis
- Unit tests and continuous integration
- Executable Python example and Jupyter notebook
- Method documentation and research roadmap

## First reproducible experiment

The first complete experiment encodes and reconstructs the quantized audio signal:

```python
samples = [3, 6, 2, 5]
```

The experiment uses:

| Item | Value |
|---|---:|
| Amplitude qubits | 3 |
| Time qubits | 2 |
| Total qubits | 5 |
| Measurement shots | 4096 |
| Simulator seed | 42 |
| Optimization level | 1 |
| Exact reconstruction | ✅ True |

### Signal reconstruction

The original and reconstructed samples are identical under ideal shot-based simulation.

![Original and reconstructed samples](figures/audio/basis_encoded_audio/reconstruction.png)

### Quantum circuit

The preparation circuit places the time register in uniform superposition and writes each quantized amplitude into the amplitude register using controlled operations. The figure is rendered with Qiskit's Matplotlib drawer and a publication-style custom color scheme.

![Colored basis-encoded quantum audio circuit](figures/audio/basis_encoded_audio/circuit_colored.png)

### Measurement distribution

The following figure shows the observed computational-basis states from 4,096 shots.

![Measurement counts](figures/audio/basis_encoded_audio/measurement_counts.png)

### Circuit resources

| Metric | Value |
|---|---:|
| Raw circuit depth | 13 |
| Raw circuit size | 17 |
| Transpiled depth | 77 |
| Transpiled size | 118 |

A scalable SVG version is available at `figures/audio/basis_encoded_audio/circuit_colored.svg`.

The complete configuration, interpretation, and machine-readable results are available in:

- [`results/audio/basis_encoded_audio/README.md`](results/audio/basis_encoded_audio/README.md)
- [`results/audio/basis_encoded_audio/experiment_report.json`](results/audio/basis_encoded_audio/experiment_report.json)
- [`examples/audio/generate_basis_audio_assets.py`](examples/audio/generate_basis_audio_assets.py)

Reproduce the full experiment with:

```bash
python examples/audio/generate_basis_audio_assets.py
```

> This experiment verifies correctness and reproducibility for a small ideal simulation. It does **not** claim quantum advantage. The next benchmarks will study scaling, finite-shot coverage, transpilation cost, and noise sensitivity.

## Controlled resource-scaling benchmark

The second reproducible experiment separates three data-loading regimes:

- **Sparse:** one set amplitude bit per sample
- **Random:** five fixed seeds reported as mean ± standard deviation
- **Dense:** all amplitude bits set

The benchmark contains **84 raw runs** and **36 aggregated conditions**. It uses a
fixed transpiler seed, three timing repetitions per run, the basis
`rz`, `sx`, `x`, and `cx`, and no statevector, shot-based, noisy, or hardware
execution.

### Signal length is the dominant pressure

With four amplitude qubits, the random profile produced:

| Samples | Total qubits | Mean transpiled depth | Mean CX count | Mean depth overhead |
|---:|---:|---:|---:|---:|
| 2 | 5 | 6.8 ± 1.6 | 3.0 ± 1.2 | 1.1 ± 0.1 |
| 8 | 7 | 393.0 ± 42.2 | 202.4 ± 23.0 | 13.2 ± 0.9 |
| 16 | 8 | 2029.8 ± 338.7 | 834.8 ± 139.7 | 32.2 ± 2.7 |
| 32 | 9 | 5759.0 ± 387.5 | 2228.4 ± 148.8 | 45.5 ± 1.7 |

From 2 to 32 samples, mean transpiled depth increased by approximately **846.9x**
and mean CX count by **742.8x**, while total qubits increased only from five to
nine.

![Controlled signal-length depth scaling](figures/audio/resource_scaling/length_transpiled_depth_profiles.png)

### Amplitude width depends strongly on loading density

For eight samples, the dense profile scaled linearly across two to eight amplitude
qubits: every additional amplitude qubit added exactly **206** layers of
transpiled depth and **110** CX gates. By contrast, the sparse profile held the
number of loaded bits fixed and remained nearly constant.

![Controlled amplitude-resolution depth scaling](figures/audio/resource_scaling/amplitude_transpiled_depth_profiles.png)

The central finding is that **qubit count alone is not a sufficient resource
indicator**. State-preparation cost is jointly determined by the width of the
time-register controls and the number of set amplitude bits.

Detailed tables and machine-readable results:

- [`results/audio/resource_scaling/README.md`](results/audio/resource_scaling/README.md)
- [`results/audio/resource_scaling/resource_scaling_summary.csv`](results/audio/resource_scaling/resource_scaling_summary.csv)
- [`results/audio/resource_scaling/resource_scaling_runs.csv`](results/audio/resource_scaling/resource_scaling_runs.csv)
- [`results/audio/resource_scaling/resource_scaling.json`](results/audio/resource_scaling/resource_scaling.json)
- [`docs/audio/resource_scaling_benchmark.md`](docs/audio/resource_scaling_benchmark.md)

Reproduce the benchmark with:

```bash
python benchmarks/audio/run_basis_resource_scaling.py
```

> These results characterize the present explicit state-preparation construction
> under a fixed software and transpiler configuration. They do not establish
> quantum advantage, hardware feasibility, execution fidelity, or asymptotic
> optimality.


## Shot-sensitivity benchmark

The third reproducible experiment evaluates finite-shot reconstruction for signals
with **4, 8, 16, and 32 samples** across shot counts from **4 to 4096**. It includes
**2,200 Monte Carlo runs**, **44 aggregated conditions**, exact theoretical
full-coverage probabilities, Wilson 95% intervals, and representative Qiskit Aer
encode-measure-decode validations.

For the present ideal basis encoding, an observed time index reveals its amplitude
deterministically. Exact reconstruction therefore requires every time index to be
observed at least once.

### Theoretical shot requirements

| Samples | Shots for ≥95% exact reconstruction | Shots for ≥99% exact reconstruction |
|---:|---:|---:|
| 4 | 16 | 21 |
| 8 | 38 | 51 |
| 16 | 90 | 115 |
| 32 | 203 | 255 |

All **44 theoretical probabilities** fell inside the corresponding empirical Wilson
95% confidence intervals. The maximum absolute empirical/theoretical mean-coverage
error was only **0.0301**.

![Exact reconstruction probability versus shots](figures/audio/shot_sensitivity/exact_reconstruction_probability.png)

The mean coverage curves also closely followed the exact expectation. Importantly,
high mean coverage does not guarantee complete reconstruction: even one unobserved
time index leaves the signal incomplete.

![Mean time-index coverage versus shots](figures/audio/shot_sensitivity/mean_time_index_coverage.png)

Both actual Qiskit validation cases achieved complete coverage, correct observed
amplitudes, and exact signal reconstruction.

Detailed results and documentation:

- [`results/audio/shot_sensitivity/README.md`](results/audio/shot_sensitivity/README.md)
- [`results/audio/shot_sensitivity/shot_sensitivity_summary.csv`](results/audio/shot_sensitivity/shot_sensitivity_summary.csv)
- [`results/audio/shot_sensitivity/shot_sensitivity_runs.csv`](results/audio/shot_sensitivity/shot_sensitivity_runs.csv)
- [`results/audio/shot_sensitivity/shot_sensitivity.json`](results/audio/shot_sensitivity/shot_sensitivity.json)
- [`docs/audio/shot_sensitivity_benchmark.md`](docs/audio/shot_sensitivity_benchmark.md)
- [`docs/audio/shot_sensitivity_analysis.md`](docs/audio/shot_sensitivity_analysis.md)

Reproduce the benchmark with:

```bash
python benchmarks/audio/run_basis_shot_sensitivity.py
```

> These results isolate ideal finite-shot sampling. They do not include gate noise,
> readout noise, backend topology, calibration drift, or real-hardware execution.


## Controlled synthetic-noise benchmark

The fourth reproducible experiment evaluates synthetic gate depolarization,
symmetric readout error, and their combination. It contains **130 noisy simulations**
and **26 aggregated conditions** for four- and eight-sample signals.

The eight-sample circuit was substantially larger:

| Samples | Total qubits | Transpiled depth | CX count |
|---:|---:|---:|---:|
| 4 | 6 | 95 | 54 |
| 8 | 7 | 454 | 236 |

At moderate gate noise, the correct-state fraction was
**0.711** for four
samples but only **0.251**
for eight samples. Moderate readout noise retained approximately
**0.941** for the
eight-sample circuit, showing that accumulated gate errors dominate this benchmark.

![Correct basis states under noise](figures/audio/noise_sensitivity/correct_basis_shot_fraction.png)

For eight samples, modal amplitude accuracy remained one through moderate gate noise
and then fell to **0.300**
at the high level and **0.050**
at the severe level.

![Modal amplitude accuracy under noise](figures/audio/noise_sensitivity/modal_amplitude_accuracy.png)

A key negative result is that four-sample exact reconstruction remained perfect even
when severe gate noise reduced the correct-state fraction to
**0.222** and increased
joint TVD to **0.778**.
Therefore, exact modal reconstruction alone can hide substantial distribution
corruption.

Detailed results and documentation:

- [`results/audio/noise_sensitivity/README.md`](results/audio/noise_sensitivity/README.md)
- [`results/audio/noise_sensitivity/noise_sensitivity_summary.csv`](results/audio/noise_sensitivity/noise_sensitivity_summary.csv)
- [`results/audio/noise_sensitivity/noise_sensitivity_runs.csv`](results/audio/noise_sensitivity/noise_sensitivity_runs.csv)
- [`results/audio/noise_sensitivity/noise_sensitivity.json`](results/audio/noise_sensitivity/noise_sensitivity.json)
- [`docs/audio/noise_sensitivity_benchmark.md`](docs/audio/noise_sensitivity_benchmark.md)
- [`docs/audio/noise_sensitivity_analysis.md`](docs/audio/noise_sensitivity_analysis.md)

Reproduce the benchmark with:

```bash
python benchmarks/audio/run_basis_noise_sensitivity.py
```

> These are controlled synthetic stress tests. They are not hardware results and
> are not derived from a particular backend calibration.


## Calibration-derived hardware-noise benchmark

The final simulation-based robustness benchmark uses `FakeNairobiV2`, a historical
seven-qubit backend snapshot, to construct an approximate Aer device-noise model.
It evaluates ideal, readout-only, gate-plus-thermal, and full-calibration conditions
across five transpiler layouts and three simulator seeds.

The hardware-mapped circuit expanded sharply with signal length:

| Samples | Logical qubits | Mean depth | Mean two-qubit gates |
|---:|---:|---:|---:|
| 4 | 6 | 188.0 | 92.8 |
| 8 | 7 | 751.8 | 432.6 |

Readout-only noise retained correct-state fractions near
**0.861** and
**0.855** for four and eight samples.
Gate-plus-thermal noise reduced them to
**0.451** and
**0.087**, respectively.

![Correct basis states under calibration-derived noise](figures/audio/hardware_noise/correct_basis_shot_fraction.png)

The four-sample circuit retained exact modal reconstruction under the full model, but
only **0.397** of measured basis states
were correct and joint TVD reached **0.603**.
The eight-sample circuit failed exact reconstruction in every full-calibration run,
with mean modal accuracy **0.158**.

![Modal reconstruction under calibration-derived noise](figures/audio/hardware_noise/modal_amplitude_accuracy.png)

Layout selection had a measurable effect for the six-logical-qubit circuit, but very
limited effect for the seven-logical-qubit circuit because it occupies the entire
backend.

![Hardware-layout sensitivity](figures/audio/hardware_noise/layout_sensitivity.png)

Detailed results and documentation:

- [`results/audio/hardware_noise/README.md`](results/audio/hardware_noise/README.md)
- [`results/audio/hardware_noise/hardware_noise_summary.csv`](results/audio/hardware_noise/hardware_noise_summary.csv)
- [`results/audio/hardware_noise/hardware_noise_layout_summary.csv`](results/audio/hardware_noise/hardware_noise_layout_summary.csv)
- [`results/audio/hardware_noise/backend_calibration.csv`](results/audio/hardware_noise/backend_calibration.csv)
- [`results/audio/hardware_noise/hardware_noise.json`](results/audio/hardware_noise/hardware_noise.json)
- [`docs/audio/calibration_hardware_noise_benchmark.md`](docs/audio/calibration_hardware_noise_benchmark.md)
- [`docs/audio/calibration_hardware_noise_analysis.md`](docs/audio/calibration_hardware_noise_analysis.md)

Reproduce the benchmark with:

```bash
python benchmarks/audio/run_basis_calibration_hardware_noise.py
```

> This experiment uses a historical backend snapshot in simulation. It is not a
> live calibration and not a real-QPU execution.

## Research questions

This repository is designed to answer questions such as:

1. How many qubits and gates are required as signal resolution increases?
2. How accurately can a signal be reconstructed from finite-shot measurements?
3. Which encoding methods remain usable after transpilation and realistic noise?
4. What is the practical cost of state preparation and readout?
5. When does a quantum representation offer a meaningful downstream benefit?

## Repository structure

```text
quantum-signal-encoding-benchmarks/
├── src/qseb/                 # Installable Python package
│   ├── audio/                # Quantum audio encodings
│   └── benchmarks/           # Reusable benchmark utilities
├── examples/audio/           # Command-line demonstrations
├── notebooks/audio/          # Reproducible notebooks
├── docs/audio/               # Mathematical and implementation notes
├── tests/audio/              # Unit and reconstruction tests
├── tests/benchmarks/         # Benchmark validation tests
├── benchmarks/               # Resource, noise, and scalability experiments
├── data/                     # Small public/example inputs only
├── results/                  # Selected reproducible benchmark reports
├── figures/                  # Selected reproducible plots and circuit figures
└── .github/workflows/        # Continuous integration
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/javad-chaharlang/quantum-signal-encoding-benchmarks.git
cd quantum-signal-encoding-benchmarks
```

### 2. Create an isolated environment

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install the project

```bash
python -m pip install --upgrade pip
pip install -e ".[dev,notebook]"
```

## Quick start

Run the compact command-line demonstration:

```bash
python examples/audio/basis_encoding_demo.py
```

Run the complete reconstruction experiment and regenerate its figures and reports:

```bash
python examples/audio/generate_basis_audio_assets.py
```

Run the controlled resource-scaling benchmark:

```bash
python benchmarks/audio/run_basis_resource_scaling.py
```

Run the shot-sensitivity benchmark:

```bash
python benchmarks/audio/run_basis_shot_sensitivity.py
```

Run the controlled synthetic-noise benchmark:

```bash
python benchmarks/audio/run_basis_noise_sensitivity.py
```

Run the calibration-derived hardware-noise benchmark:

```bash
python benchmarks/audio/run_basis_calibration_hardware_noise.py
```

Minimal Python usage:

```python
from qseb.audio import (
    build_basis_encoded_audio_circuit,
    reconstruct_from_counts,
    simulate_counts,
)

samples = [3, 6, 2, 5]
circuit, spec = build_basis_encoded_audio_circuit(samples, amplitude_bits=3)
counts = simulate_counts(circuit, shots=4096, seed_simulator=42)
reconstructed = reconstruct_from_counts(counts, spec)

print(reconstructed)
```

## Reproducibility

Every benchmark should record:

- Software and Python versions
- Input data and preprocessing
- Random seeds
- Number of shots
- Simulator or backend
- Transpiler optimization level
- Qubit count, circuit depth, and operation counts
- Reconstruction metrics
- Noise-model assumptions
- Hardware limitations and negative results

Generated results should not be committed without the corresponding script, configuration, and seed.

## Roadmap

| Phase | Method or topic | Status |
|---|---|---|
| Audio foundations | Basis-encoded audio implementation | ✅ Implemented |
| Audio foundations | Reproducible visual experiment | ✅ Implemented |
| Benchmarking | Controlled resource scaling | ✅ Implemented |
| Benchmarking | Shot sensitivity | ✅ Implemented |
| Benchmarking | Synthetic noise sensitivity | ✅ Implemented |
| Benchmarking | Calibration-derived hardware noise | ✅ Implemented |
| Benchmarking | Real-QPU execution | ⏳ Future extension |
| Audio representations | QRDA | ⏳ Planned |
| Audio representations | FRQA | ⏳ Planned |
| Audio representations | QPAM / SQPAM | ⏳ Planned |
| Image representations | FRQI | ⏳ Planned |
| Image representations | NEQR | ⏳ Planned |
| Image representations | QPIE / amplitude encoding | ⏳ Planned |
| Applications | Hybrid quantum medical imaging | 🔭 Future phase |
| Applications | Secure quantum multimedia processing | 🔭 Future phase |

See [ROADMAP.md](ROADMAP.md) for the detailed research plan.

## Scientific integrity

- Primary papers are cited for every reproduced method.
- Reimplementations are identified explicitly and do not claim ownership of the original method.
- Code, figures, and text from other projects are not copied without compatible licensing and attribution.
- Simulator results are not presented as hardware results.
- Quantum advantage is not claimed without strong classical baselines and full resource accounting.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Until an archival release and DOI are available, cite the repository as:

> Javad Chaharlang. *Quantum Signal Encoding Benchmarks: Reproducible Qiskit Implementations for Quantum Audio and Image Representations*. GitHub repository, 2026.

## Contributing

Contributions that improve correctness, testing, documentation, or benchmarking are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

Licensed under the [Apache License 2.0](LICENSE).

## Author

**Javad Chaharlang, Ph.D.**  
Research Scientist — Quantum Machine Learning, Quantum Signal Processing, AI, and Secure Multimedia Processing

- GitHub: [javad-chaharlang](https://github.com/javad-chaharlang)
- LinkedIn: [Javad Chaharlang](https://www.linkedin.com/in/javad-chaharlang-ph-d-7b417555/)
