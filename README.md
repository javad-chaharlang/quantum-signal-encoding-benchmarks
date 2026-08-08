# Quantum Signal Encoding Benchmarks

[![CI](https://github.com/javad-chaharlang/quantum-signal-encoding-benchmarks/actions/workflows/ci.yml/badge.svg)](https://github.com/javad-chaharlang/quantum-signal-encoding-benchmarks/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.4%2B-6929C4.svg)](https://www.ibm.com/quantum/qiskit)
[![License](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![Research Software](https://img.shields.io/badge/Research-Reproducible-informational.svg)](#reproducibility)

A reproducible research repository for implementing and benchmarking **quantum representations of classical signals** with Qiskit. The project begins with quantum audio and image encoding and then progresses toward hybrid quantum-classical learning, medical imaging, and secure quantum multimedia processing.

> **Research principle:** an encoding method is not considered complete until its state definition, circuit preparation, decoding procedure, reconstruction accuracy, resource requirements, and noise sensitivity are documented.

## Research direction

This repository is **not intended to become an exhaustive collection of quantum signal-representation implementations**. Published audio and image representations are treated as validated research baselines: they are reproduced, tested, visualized, and critically assessed only to the depth needed to support the project's main trajectory.

The current research path is:

**validated representations → critical security-suitability analysis → quantum steganography/watermarking → quantum steganalysis → secure quantum medical imaging**

QRDA is the first completed baseline. Operations such as QRDA connection, mixing, and compression are no longer mandatory roadmap milestones; they will be implemented only if a downstream security or medical-imaging experiment requires them.

The next representation work therefore prioritizes **FRQA for signed-audio comparison**, followed by selected quantum-image baselines such as **FRQI and NEQR**, before moving into representation suitability for secure quantum multimedia.

See:

- [`ROADMAP.md`](ROADMAP.md) for the updated milestone structure
- [`docs/research_direction.md`](docs/research_direction.md) for the scientific scope and decision rules
- [`docs/linkedin_research_series.md`](docs/linkedin_research_series.md) for the evidence-based research communication plan

## Current release: v0.2.1

Version 0.2.1 completes the repository's **primary-paper validation of QRDA** and extends the encoder from the earlier power-of-two case to the full QRDA $2^l$-box construction for arbitrary positive signal lengths.

For an effective signal of length $L$, the QRDA time-register width is

```math
l=
\begin{cases}
\lceil \log_2 L\rceil, & L>1,\\
1, & L=1.
\end{cases}
```

The complete encoded state is

```math
\left|B\right\rangle
=
\frac{1}{\sqrt{2^l}}
\left(
\sum_{t=0}^{L-1}
\left|S_t\right\rangle_{\mathrm{amp}}
\otimes
\left|t\right\rangle_{\mathrm{time}}
+
\sum_{t=L}^{2^l-1}
\left|0\right\rangle^{\otimes m}_{\mathrm{amp}}
\otimes
\left|t\right\rangle_{\mathrm{time}}
\right),
```

where:

- $L$ is the number of effective audio samples;
- $m$ is the number of qubits in the amplitude register;
- $l$ is the number of qubits in the time register;
- $S_t$ is the unsigned quantized amplitude associated with effective time index $t$;
- $2^l-L$ is the number of redundant QRDA box positions.

The encoder accepts unsigned quantized amplitudes in the range

```math
0 \leq S_t \leq 2^m-1.
```

For a signed $m$-bit sample $x_t$, the repository provides explicit preprocessing helpers implementing

```math
S_t=x_t+2^{m-1},
```

with inverse reconstruction

```math
x_t=S_t-2^{m-1}.
```

The encoder itself remains unsigned; signed/unsigned translation is a separate, validated preprocessing layer.

### Included in v0.2.1

- Full arbitrary-length QRDA $2^l$-box support
- Explicit `box_size`, `padding_count`, and `padding_fraction` metadata
- Correct $L=1$ handling with one time qubit
- Validated signed-to-unsigned and unsigned-to-signed audio translation
- Exact reproduction of the primary paper's 15-sample, 4-bit worked example
- 8-qubit paper-example circuit: 4 amplitude qubits + 4 time qubits
- One redundant QRDA box state at $T=15$ with amplitude zero
- Independently constructed reference state with fidelity 1.0
- Exact logical controlled-write count of 33, matching the paper
- Explicit mapping from open/closed controls to Qiskit `X`-conjugated `mcx`
- Exact unsigned and signed shot-based round-trip reconstruction
- Machine-readable validation and circuit-metric outputs
- Backward-compatible legacy basis-encoding API
- Existing resource, shot, synthetic-noise, and calibration-derived hardware-noise benchmarks
- Unit tests and continuous integration

### Primary QRDA reference

Wang, J. (2016). QRDA: Quantum Representation of Digital Audio. *International Journal of Theoretical Physics, 55*, 1622–1641. https://doi.org/10.1007/s10773-015-2800-2

## QRDA API

New code should use the QRDA-specific public API:

```python
from qseb.audio import (
    QRDAEncodingSpec,
    build_qrda_circuit,
    decode_qrda_counts,
    exact_qrda_probabilities,
    qrda_offset,
    qrda_resource_metrics,
    reconstruct_qrda_signal,
    signed_amplitude_range,
    signed_to_unsigned_samples,
    simulate_qrda_counts,
    unsigned_amplitude_range,
    unsigned_to_signed_samples,
)
```

The historical basis-encoding names remain available as aliases so existing scripts and notebooks continue to work.

## Primary-paper QRDA validation

Version 0.2.1 reproduces the worked QRDA example from the primary paper.

The original signed 4-bit signal is

```text
[0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0]
```

and the QRDA offset translation produces

```text
[8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8]
```

The validated configuration is:

| Item | Validated value |
|---|---:|
| Effective samples | 15 |
| Amplitude qubits | 4 |
| Time qubits | 4 |
| Total qubits | 8 |
| QRDA box size | 16 |
| Padding states | 1 |
| Nonzero state support | 16 |
| Probability per QRDA box state | 0.0625 |
| State fidelity to independent reference | 1.0 |
| Paper logical controlled writes | 33 |
| Repository logical `mcx` writes | 33 |
| Zero-control `X` wrappers | 64 |
| Exact unsigned reconstruction | ✅ |
| Exact signed reconstruction | ✅ |

The repository distinguishes **state equivalence**, **logical preparation equivalence**, and **physical transpiled gate decomposition**. The 33 symbolic controlled writes reported by the paper are therefore not equated with the final transpiled CX count.

Reproduce the worked example with:

```bash
python examples/audio/reproduce_qrda_primary_paper.py
```

Reproduce the preparation-protocol comparison with:

```bash
python benchmarks/audio/run_qrda_protocol_comparison.py
```

Validation outputs:

- [`results/audio/qrda_primary_paper/validation_report.json`](results/audio/qrda_primary_paper/validation_report.json)
- [`results/audio/qrda_primary_paper/statevector_support.csv`](results/audio/qrda_primary_paper/statevector_support.csv)
- [`results/audio/qrda_primary_paper/protocol_comparison.json`](results/audio/qrda_primary_paper/protocol_comparison.json)
- [`results/audio/qrda_primary_paper/protocol_mapping.csv`](results/audio/qrda_primary_paper/protocol_mapping.csv)
- [`results/audio/qrda_primary_paper/circuit_metrics.csv`](results/audio/qrda_primary_paper/circuit_metrics.csv)
- [`docs/audio/qrda_primary_paper_validation.md`](docs/audio/qrda_primary_paper_validation.md)

> The implementation reproduces the paper's QRDA state and logical amplitude-loading protocol. It does not claim physical gate-for-gate identity with the paper diagram.

## QRDA primary-paper visual validation

The validated 15-sample primary-paper example is also available as a reproducible visual package. The figures below are generated by `examples/audio/generate_qrda_primary_paper_assets.py` and correspond to the same QRDA state, register convention, signed/unsigned preprocessing, and logical preparation protocol reported above.

### Logical 8-qubit QRDA circuit

The paper example uses four amplitude qubits and four time qubits. Hadamard gates create the uniform time-register superposition, while the controlled amplitude-loading operations write the unsigned quantized sample values into the amplitude register.

![QRDA primary-paper logical circuit](figures/audio/qrda_primary_paper/qrda_logical_circuit.png)

A scalable vector version is available at [`qrda_logical_circuit.svg`](figures/audio/qrda_primary_paper/qrda_logical_circuit.svg).

### Transpiled QRDA circuits

The logical circuit is also transpiled to the fixed basis `rz`, `sx`, `x`, and `cx` at optimization levels 0 and 1. These physical decompositions are implementation- and transpiler-configuration-dependent and are not claimed to be gate-for-gate identical to the symbolic circuit in the primary paper.

<details>
<summary><strong>Optimization level 0</strong></summary>

![QRDA transpiled circuit optimization level 0](figures/audio/qrda_primary_paper/qrda_transpiled_o0.png)

[Open scalable SVG](figures/audio/qrda_primary_paper/qrda_transpiled_o0.svg)

</details>

<details>
<summary><strong>Optimization level 1</strong></summary>

![QRDA transpiled circuit optimization level 1](figures/audio/qrda_primary_paper/qrda_transpiled_o1.png)

[Open scalable SVG](figures/audio/qrda_primary_paper/qrda_transpiled_o1.svg)

</details>

### Signed-to-unsigned QRDA preprocessing

The original signed 4-bit waveform and its QRDA-compatible unsigned translation are shown together.

![Signed-to-unsigned QRDA preprocessing](figures/audio/qrda_primary_paper/signed_unsigned_signal.png)

### Exact QRDA state support

The full QRDA box contains 16 equally weighted basis states, including the redundant time position at $T=15$ with zero amplitude.

![Exact QRDA state support](figures/audio/qrda_primary_paper/state_support.png)

### Exact round-trip reconstruction

The reconstructed signed signal coincides with the original 15-sample signal.

![QRDA signed reconstruction](figures/audio/qrda_primary_paper/reconstruction_signed.png)

The corresponding unsigned reconstruction is available at [`reconstruction_unsigned.png`](figures/audio/qrda_primary_paper/reconstruction_unsigned.png).

### Logical preparation-protocol comparison

The visual comparison separates the paper's abstract logical preparation counts from Qiskit's explicit logical operations. The 33 controlled amplitude writes are reproduced without equating them to the final transpiled CX count.

![QRDA logical preparation-protocol comparison](figures/audio/qrda_primary_paper/protocol_comparison.png)

Generate the complete visual package with:

```bash
python -m pip install -e ".[dev,notebook]"
python examples/audio/generate_qrda_primary_paper_assets.py
```

Visual outputs and the machine-readable visual-assets report are documented in [`results/audio/qrda_primary_paper/README.md`](results/audio/qrda_primary_paper/README.md).

## First reproducible QRDA experiment

The first complete experiment encodes and reconstructs the unsigned quantized signal

```python
samples = [3, 6, 2, 5]
```

with the following configuration:

| Item | Value |
|---|---:|
| Amplitude qubits | 3 |
| Time qubits | 2 |
| Total qubits | 5 |
| Measurement shots | 4096 |
| Simulator seed | 42 |
| Transpiler optimization level | 1 |
| Exact reconstruction | ✅ True |

### Signal reconstruction

The original and reconstructed samples are identical under ideal shot-based simulation.

![Original and reconstructed QRDA samples](figures/audio/basis_encoded_audio/reconstruction.png)

### Quantum circuit

The preparation circuit places the time register in uniform superposition and conditionally writes each unsigned quantized amplitude into the amplitude register.

![Colored QRDA quantum audio circuit](figures/audio/basis_encoded_audio/circuit_colored.png)

### Measurement distribution

The following figure shows the observed computational-basis states from 4,096 shots.

![QRDA measurement counts](figures/audio/basis_encoded_audio/measurement_counts.png)

### Circuit resources

| Metric | Value |
|---|---:|
| Raw circuit depth | 13 |
| Raw circuit size | 17 |
| Transpiled depth | 77 |
| Transpiled size | 118 |

A scalable circuit figure is available at `figures/audio/basis_encoded_audio/circuit_colored.svg`.

The full configuration, report, and generation script are available in:

- [`results/audio/basis_encoded_audio/README.md`](results/audio/basis_encoded_audio/README.md)
- [`results/audio/basis_encoded_audio/experiment_report.json`](results/audio/basis_encoded_audio/experiment_report.json)
- [`examples/audio/generate_basis_audio_assets.py`](examples/audio/generate_basis_audio_assets.py)

The historical `basis_encoded_audio` paths and `basis_*` script names are retained for backward compatibility. Their current implementation evaluates the QRDA state representation.

Reproduce the experiment with:

```bash
python examples/audio/generate_basis_audio_assets.py
```

> This experiment verifies correctness and reproducibility for a small ideal simulation. It does **not** claim quantum advantage.

## Controlled resource-scaling benchmark

The resource-scaling benchmark separates three data-loading regimes:

- **Sparse:** one set amplitude bit per sample;
- **Random:** five fixed random seeds reported as mean ± standard deviation;
- **Dense:** all amplitude bits set.

The benchmark contains **84 raw runs** and **36 aggregated conditions**. It uses a fixed transpiler seed, three timing repetitions per run, the basis gates `rz`, `sx`, `x`, and `cx`, and no statevector, shot-based, noisy, or hardware execution.

### Signal length is the dominant pressure

With four amplitude qubits, the random profile produced:

| Samples | Total qubits | Mean transpiled depth | Mean CX count | Mean depth overhead |
|---:|---:|---:|---:|---:|
| 2 | 5 | 6.8 ± 1.6 | 3.0 ± 1.2 | 1.1 ± 0.1 |
| 8 | 7 | 393.0 ± 42.2 | 202.4 ± 23.0 | 13.2 ± 0.9 |
| 16 | 8 | 2029.8 ± 338.7 | 834.8 ± 139.7 | 32.2 ± 2.7 |
| 32 | 9 | 5759.0 ± 387.5 | 2228.4 ± 148.8 | 45.5 ± 1.7 |

From 2 to 32 samples, mean transpiled depth increased by approximately **846.9×** and mean CX count by **742.8×**, while total qubits increased only from five to nine.

![Controlled QRDA signal-length depth scaling](figures/audio/resource_scaling/length_transpiled_depth_profiles.png)

### Amplitude width depends on loading density

For eight samples, the dense profile scaled linearly across two to eight amplitude qubits: every additional amplitude qubit added exactly **206** layers of transpiled depth and **110** CX gates. By contrast, the sparse profile kept the number of loaded bits fixed and remained nearly constant.

![Controlled QRDA amplitude-resolution depth scaling](figures/audio/resource_scaling/amplitude_transpiled_depth_profiles.png)

The central finding is that **qubit count alone is not a sufficient resource indicator**. QRDA state-preparation cost is jointly determined by the width of the time-register controls and the number of set amplitude bits.

Detailed results and documentation:

- [`results/audio/resource_scaling/README.md`](results/audio/resource_scaling/README.md)
- [`results/audio/resource_scaling/resource_scaling_summary.csv`](results/audio/resource_scaling/resource_scaling_summary.csv)
- [`results/audio/resource_scaling/resource_scaling_runs.csv`](results/audio/resource_scaling/resource_scaling_runs.csv)
- [`results/audio/resource_scaling/resource_scaling.json`](results/audio/resource_scaling/resource_scaling.json)
- [`docs/audio/resource_scaling_benchmark.md`](docs/audio/resource_scaling_benchmark.md)

Reproduce the benchmark with:

```bash
python benchmarks/audio/run_basis_resource_scaling.py
```

> These results characterize the present explicit QRDA state-preparation construction under a fixed software and transpiler configuration. They do not establish quantum advantage, hardware feasibility, execution fidelity, or asymptotic optimality.

## Shot-sensitivity benchmark

The shot-sensitivity benchmark evaluates finite-shot reconstruction for signals with **4, 8, 16, and 32 samples** across shot counts from **4 to 4096**. It includes **2,200 Monte Carlo runs**, **44 aggregated conditions**, exact theoretical full-coverage probabilities, Wilson 95% intervals, and representative Qiskit Aer encode-measure-decode validations.

For the current ideal QRDA encoding, observing a time index reveals its associated unsigned amplitude deterministically. Exact reconstruction therefore requires every time index to be observed at least once.

For $N$ equally likely time indices and $M$ measurement shots, the exact probability of observing every time index is

```math
P_{\mathrm{full}}(N,M)
=
\frac{N!}{N^M}
\left\{\begin{matrix}M\\N\end{matrix}\right\},
```

where the braces denote a Stirling number of the second kind.

### Theoretical shot requirements

| Samples | Shots for ≥95% exact reconstruction | Shots for ≥99% exact reconstruction |
|---:|---:|---:|
| 4 | 16 | 21 |
| 8 | 38 | 51 |
| 16 | 90 | 115 |
| 32 | 203 | 255 |

All **44 theoretical probabilities** fell inside the corresponding empirical Wilson 95% confidence intervals. The maximum absolute empirical/theoretical mean-coverage error was **0.0301**.

![QRDA exact reconstruction probability versus shots](figures/audio/shot_sensitivity/exact_reconstruction_probability.png)

The mean-coverage curves also closely followed the exact expectation. High mean coverage does not guarantee complete reconstruction: one unobserved time index is sufficient to leave the signal incomplete.

![QRDA mean time-index coverage versus shots](figures/audio/shot_sensitivity/mean_time_index_coverage.png)

Both Qiskit validation cases achieved complete coverage, correct observed amplitudes, and exact signal reconstruction.

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

> These results isolate ideal finite-shot sampling. They do not include gate noise, readout noise, backend topology, calibration drift, or real-hardware execution.

## Controlled synthetic-noise benchmark

The synthetic-noise benchmark evaluates gate depolarization, symmetric readout error, and their combination. It contains **130 noisy simulations** and **26 aggregated conditions** for four- and eight-sample signals.

The eight-sample circuit was substantially larger:

| Samples | Total qubits | Transpiled depth | CX count |
|---:|---:|---:|---:|
| 4 | 6 | 95 | 54 |
| 8 | 7 | 454 | 236 |

At moderate gate noise, the correct-state fraction was **0.711** for four samples but only **0.251** for eight samples. Moderate readout noise retained approximately **0.941** for the eight-sample circuit, showing that accumulated gate errors dominate this benchmark.

![Correct QRDA computational-basis states under noise](figures/audio/noise_sensitivity/correct_basis_shot_fraction.png)

For eight samples, modal amplitude accuracy remained one through moderate gate noise and then fell to **0.300** at the high level and **0.050** at the severe level.

![QRDA modal amplitude accuracy under noise](figures/audio/noise_sensitivity/modal_amplitude_accuracy.png)

A key negative result is that four-sample exact reconstruction remained perfect even when severe gate noise reduced the correct-state fraction to **0.222** and increased joint total variation distance to **0.778**. Exact modal reconstruction alone can therefore hide substantial distribution corruption.

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

> These are controlled synthetic stress tests. They are not hardware results and are not derived from a particular backend calibration.

## Calibration-derived hardware-noise benchmark

The final simulation-based robustness benchmark uses `FakeNairobiV2`, a historical seven-qubit backend snapshot, to construct an approximate Qiskit Aer device-noise model. It evaluates ideal, readout-only, gate-plus-thermal, and full-calibration conditions across five transpiler layouts and three simulator seeds.

The hardware-mapped circuit expanded sharply with signal length:

| Samples | Logical qubits | Mean depth | Mean two-qubit gates |
|---:|---:|---:|---:|
| 4 | 6 | 188.0 | 92.8 |
| 8 | 7 | 751.8 | 432.6 |

Readout-only noise retained correct-state fractions near **0.861** and **0.855** for four and eight samples. Gate-plus-thermal noise reduced them to **0.451** and **0.087**, respectively.

![Correct QRDA computational-basis states under calibration-derived noise](figures/audio/hardware_noise/correct_basis_shot_fraction.png)

The four-sample circuit retained exact modal reconstruction under the full model, but only **0.397** of measured basis states were correct and joint total variation distance reached **0.603**. The eight-sample circuit failed exact reconstruction in every full-calibration run, with mean modal accuracy **0.158**.

![QRDA modal reconstruction under calibration-derived noise](figures/audio/hardware_noise/modal_amplitude_accuracy.png)

Layout selection had a measurable effect for the six-logical-qubit circuit but a limited effect for the seven-logical-qubit circuit because it occupies the entire backend.

![QRDA hardware-layout sensitivity](figures/audio/hardware_noise/layout_sensitivity.png)

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

> This experiment uses a historical backend snapshot in simulation. It is not a live calibration and not a real-QPU execution.

## Research questions

This repository is designed to answer questions such as:

1. How many qubits and gates are required as signal resolution increases?
2. How accurately can a signal be reconstructed from finite-shot measurements?
3. Which encoding methods remain usable after transpilation and realistic noise?
4. What is the practical cost of state preparation and readout?
5. How strongly do data patterns affect state-preparation resources?
6. When does a quantum representation provide a meaningful downstream benefit?

## Repository structure

```text
quantum-signal-encoding-benchmarks/
├── src/qseb/                 # Installable Python package
│   ├── audio/                # Quantum audio representations
│   └── benchmarks/           # Reusable benchmark utilities
├── examples/audio/           # Command-line demonstrations
├── notebooks/audio/          # Reproducible notebooks
├── docs/audio/               # Mathematical and implementation notes
├── tests/audio/              # Unit and reconstruction tests
├── tests/benchmarks/         # Benchmark validation tests
├── benchmarks/               # Resource, shot, noise, and scalability studies
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

### Minimal QRDA example

```python
from qseb.audio import (
    build_qrda_circuit,
    reconstruct_qrda_signal,
    simulate_qrda_counts,
)

samples = [3, 6, 2, 5]

circuit, spec = build_qrda_circuit(samples, amplitude_bits=3)
counts = simulate_qrda_counts(
    circuit,
    shots=4096,
    seed_simulator=42,
)
reconstructed = reconstruct_qrda_signal(counts, spec)

print(reconstructed)
```

Expected output:

```text
[3, 6, 2, 5]
```

### Primary-paper reproduction

```bash
python examples/audio/reproduce_qrda_primary_paper.py
python benchmarks/audio/run_qrda_protocol_comparison.py
```

These commands validate the 15-sample primary-paper example, full $2^l$-box support, padding state, state fidelity, logical controlled-write count, and transpiled circuit metrics.

### Legacy command-line entry points

Run the compact command-line demonstration:

```bash
python examples/audio/basis_encoding_demo.py
```

Regenerate the complete reconstruction experiment, figures, and reports:

```bash
python examples/audio/generate_basis_audio_assets.py
```

Run the resource-scaling benchmark:

```bash
python benchmarks/audio/run_basis_resource_scaling.py
```

Run the shot-sensitivity benchmark:

```bash
python benchmarks/audio/run_basis_shot_sensitivity.py
```

Run the synthetic-noise benchmark:

```bash
python benchmarks/audio/run_basis_noise_sensitivity.py
```

Run the calibration-derived hardware-noise benchmark:

```bash
python benchmarks/audio/run_basis_calibration_hardware_noise.py
```

The `basis_*` filenames are legacy entry points retained to avoid breaking earlier commands. New Python code should use the QRDA-specific public API.

### Legacy API compatibility

Existing imports remain valid:

```python
from qseb.audio import (
    build_basis_encoded_audio_circuit,
    reconstruct_from_counts,
    simulate_counts,
)
```

The legacy names are aliases for the same validated implementation.

## Testing and quality checks

Run the complete test suite:

```bash
python -m pytest
```

Run lint checks:

```bash
python -m ruff check .
```

Check formatting:

```bash
python -m ruff format --check .
```

The continuous-integration workflow runs installation, linting, formatting, and tests on Python 3.10, 3.11, and 3.12.

## Reproducibility

Every benchmark should record:

- software and Python versions;
- input data and preprocessing;
- random seeds;
- number of measurement shots;
- simulator or backend;
- transpiler optimization level and seed;
- qubit count, circuit depth, and operation counts;
- reconstruction metrics;
- noise-model assumptions;
- calibration metadata when applicable;
- hardware limitations and negative results.

Generated results should not be committed without the corresponding script, configuration, and seed.

## Roadmap

| Phase | Method or topic | Status |
|---|---|---|
| Audio representations | QRDA arbitrary-length $2^l$-box implementation | ✅ v0.2.1 |
| Audio representations | QRDA exact published-example validation | ✅ v0.2.1 |
| Audio representations | QRDA preparation-protocol comparison | ✅ v0.2.1 |
| Audio foundations | Reproducible QRDA visual experiment | ✅ Implemented |
| Benchmarking | Controlled QRDA resource scaling | ✅ Implemented |
| Benchmarking | QRDA shot sensitivity | ✅ Implemented |
| Benchmarking | QRDA synthetic-noise sensitivity | ✅ Implemented |
| Benchmarking | QRDA calibration-derived hardware noise | ✅ Implemented |
| Benchmarking | Real-QPU execution | ⏳ Future extension |
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
- State and logical-protocol equivalence are distinguished explicitly from physical gate-for-gate identity after transpilation.
- Code, figures, and text from other projects are not copied without compatible licensing and attribution.
- Simulator results are not presented as hardware results.
- Historical calibration snapshots are not presented as live backend calibrations.
- Quantum advantage is not claimed without strong classical baselines and complete resource accounting.
- Negative results and practical limitations are retained in reports.

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
