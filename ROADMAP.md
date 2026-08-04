# Research Roadmap

This roadmap organizes the project as a progression from **encoding** to **benchmarking**, then to **learning** and **security**.

## Phase 1 — Quantum audio representations

### 1. Basis-encoded audio

- [x] Mathematical state definition
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
- [ ] Noise-model experiment
- [ ] Hardware-aware transpilation study

### 2. QRDA

- [ ] Review and cite the primary paper
- [ ] Reproduce the exact state definition
- [ ] Implement amplitude and time registers
- [ ] Add decoding and reconstruction
- [ ] Validate against published examples
- [ ] Compare with basis encoding

### 3. FRQA

- [ ] Exact signed-amplitude representation
- [ ] State preparation and inverse reconstruction
- [ ] Comparison with QRDA
- [ ] Scaling and noise analysis

### 4. QPAM and SQPAM

- [ ] Probability-amplitude encoding
- [ ] Shot-complexity analysis
- [ ] Reconstruction error analysis
- [ ] Comparative benchmark

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
- [ ] Unified experiment configuration across encoding methods
- [ ] Qubit and ancilla counts across methods
- [ ] State-preparation complexity comparison
- [x] Shot sensitivity for the basis-encoded baseline
- [ ] Noise sensitivity
- [ ] Reconstruction fidelity and error
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

- **v0.1:** Basis-encoded audio foundation
- **v0.1.1:** Controlled resource-scaling benchmark
- **v0.1.2:** Shot-sensitivity and full-coverage benchmark
- **v0.2:** Exact QRDA implementation
- **v0.3:** FRQA and comparative audio benchmark
- **v0.4:** FRQI and NEQR
- **v0.5:** Audio/image resource and noise benchmark report
