# Research Roadmap

This roadmap organizes the project as a progression from **encoding** to **benchmarking**, then to **learning** and **security**.

## Phase 1 — Quantum audio representations

### 1. QRDA

- [x] Mathematical state definition
- [x] Unsigned amplitude and time registers
- [x] State-preparation circuit
- [x] Exact statevector validation
- [x] Shot-based simulation
- [x] Decoding and reconstruction
- [x] Resource metrics
- [x] Controlled signal-length and amplitude-resolution scaling study
- [x] Sparse, repeated-random, and dense loading profiles
- [x] Raw and basis-transpiled depth, size, and CX accounting
- [x] Controlled shot-sensitivity experiment
- [x] Exact full-coverage probability and theoretical shot thresholds
- [x] Monte Carlo confidence intervals and Qiskit validation
- [x] Controlled synthetic noise-model experiment
- [x] Gate, readout, and combined error families
- [x] Reconstruction, bit-error, and distribution metrics
- [x] Calibration-derived backend noise model
- [x] Gate, thermal-relaxation, and readout ablations
- [x] Hardware-aware transpilation and physical-layout study
- [x] Calibration record and circuit-exposure reporting
- [x] QRDA-specific API and backward-compatible legacy aliases
- [x] Unsigned-amplitude and bipolar-offset documentation
- [ ] Reproduce the primary paper's exact worked example
- [ ] Compare the implemented preparation circuit with the paper protocol
- [ ] Real-QPU execution with a live calibration snapshot
- [ ] Real-QPU error-mitigation comparison

### 2. FRQA

- [ ] Review and cite the primary paper
- [ ] Implement exact signed-amplitude representation
- [ ] Implement state preparation and inverse reconstruction
- [ ] Add exact statevector validation
- [ ] Add shot-based reconstruction tests
- [ ] Compare qubit requirements with QRDA
- [ ] Compare state-preparation complexity with QRDA
- [ ] Perform scaling and noise analysis

### 3. QPAM and SQPAM

- [ ] Review and cite the primary papers
- [ ] Implement probability-amplitude encoding
- [ ] Implement decoding and reconstruction
- [ ] Analyze shot complexity
- [ ] Analyze reconstruction error
- [ ] Compare QPAM and SQPAM with QRDA and FRQA

## Phase 2 — Quantum image representations

- [ ] FRQI
- [ ] NEQR
- [ ] QPIE / amplitude encoding
- [ ] Grayscale and small medical-image examples
- [ ] Resource and reconstruction benchmark
- [ ] Noise-aware evaluation

## Phase 3 — Cross-method benchmark suite

- [x] Reusable resource-scaling utilities
- [x] Deterministic benchmark profiles and seeds
- [x] Raw and basis-transpiled circuit depth
- [x] One- and two-qubit operation counts
- [x] Shot sensitivity for the QRDA baseline
- [x] Synthetic noise sensitivity for the QRDA baseline
- [x] Calibration-derived hardware-noise sensitivity for the QRDA baseline
- [ ] Unified experiment configuration across encoding methods
- [ ] Qubit and ancilla counts across methods
- [ ] State-preparation complexity comparison
- [ ] Reconstruction fidelity and error comparison
- [ ] Real-QPU execution and mitigation benchmark
- [ ] Reproducible cross-method benchmark report

## Phase 4 — Hybrid quantum medical imaging

- [ ] Classical feature extractor + variational quantum classifier
- [ ] Quantum kernel benchmark
- [ ] Quanvolution benchmark
- [ ] Data-scarce medical imaging experiments
- [ ] Strong size-matched classical baselines
- [ ] Multiple seeds and confidence intervals
- [ ] Ablation and resource accounting

## Phase 5 — Secure quantum multimedia processing

- [ ] Threat-model-driven quantum multimedia security
- [ ] Quantum watermarking and steganalysis as specialist studies
- [ ] Post-quantum-secured medical-data pipelines
- [ ] Robustness, attack, and provenance evaluation

## Release targets

- **v0.1:** Unsigned amplitude/time audio foundation
- **v0.1.1:** Controlled resource-scaling benchmark
- **v0.1.2:** Shot-sensitivity and full-coverage benchmark
- **v0.1.3:** Controlled synthetic-noise benchmark
- **v0.1.4:** Calibration-derived hardware-noise benchmark
- **v0.2:** QRDA state-representation formalization and validation
- **v0.2.1:** Primary-paper QRDA example and gate-protocol validation
- **v0.3:** FRQA and comparative audio benchmark
- **v0.4:** FRQI and NEQR
- **v0.5:** Audio/image resource and noise benchmark report
