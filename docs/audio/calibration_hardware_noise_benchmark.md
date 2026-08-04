# Calibration-Derived Hardware-Noise Benchmark

## Objective

This final basis-encoding benchmark replaces manually selected synthetic error
probabilities with an approximate device noise model generated from a historical IBM
backend snapshot.

## Backend snapshot

The experiment uses:

```text
qiskit_ibm_runtime.fake_provider.FakeNairobiV2
```

This is a seven-qubit `BackendV2` snapshot. It contains:

- coupling-map and target constraints;
- qubit frequencies and relaxation properties when available;
- instruction durations and average instruction errors;
- per-qubit measurement error information.

It does not provide a live view of a currently operating QPU.

## Noise-model construction

Qiskit Aer's `NoiseModel.from_backend()` constructs an approximate device model from
the snapshot. The full model combines:

- calibration-derived depolarizing gate errors;
- thermal-relaxation errors derived from gate duration, T1, and T2;
- single-qubit readout errors.

The benchmark also includes two ablations:

- `readout_only`;
- `gate_thermal`.

Every noisy condition is compared with ideal execution of the same hardware-mapped
transpiled circuit.

## Hardware-aware layout experiment

Calibration parameters are qubit- and edge-specific. Therefore, five transpiler
seeds are used:

```text
42, 52, 62, 72, 82
```

Three simulator seeds are evaluated for every layout:

```text
42, 52, 62
```

## Experiment grid

- Signal lengths: `4`, `8`
- Amplitude width: `4` qubits
- Logical qubits: `6`, `7`
- Shots: `2048`
- Noise conditions: `4`
- Layout seeds: `5`
- Simulator seeds: `3`
- Raw runs: `2 × 4 × 5 × 3 = 120`
- Global aggregated conditions: `8`
- Layout-level aggregated conditions: `40`

## Metrics

The benchmark retains all reconstruction and distribution metrics from the synthetic
noise study and adds:

- initial and final physical layouts;
- transpiled depth and size;
- two-qubit gate and SWAP counts;
- mean and maximum selected-qubit readout error;
- mean selected-qubit T1 and T2;
- summed calibrated instruction-error budget;
- an independent-gate success proxy;
- total calibrated instruction duration.

The independent-gate success proxy is a diagnostic heuristic, not a circuit-fidelity
estimate.

## Install

The fake backend is distributed through `qiskit-ibm-runtime`:

```bash
pip install -e ".[dev,notebook]"
```

No IBM Quantum token is required for the bundled historical snapshot.

## Run

```bash
python benchmarks/audio/run_basis_calibration_hardware_noise.py
```

## Expected outputs

```text
results/audio/hardware_noise/
├── README.md
├── backend_calibration.csv
├── hardware_noise.json
├── hardware_noise_layout_summary.csv
├── hardware_noise_runs.csv
└── hardware_noise_summary.csv

figures/audio/hardware_noise/
├── correct_basis_shot_fraction.png
├── exact_reconstruction_rate.png
├── joint_distribution_tvd.png
├── layout_sensitivity.png
└── modal_amplitude_accuracy.png
```

## Interpretation boundary

Automatic device models are approximate. They do not model all correlated errors,
crosstalk, leakage, calibration drift, pulse-level effects, or workload-dependent
behavior. Results from the historical fake backend must not be presented as current
or direct hardware measurements.
