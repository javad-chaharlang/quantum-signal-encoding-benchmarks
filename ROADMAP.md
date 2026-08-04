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
- [ ] Shot-sensitivity experiment
- [ ] Noise-model experiment
- [ ] Scaling study

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

- [ ] Unified experiment configuration
- [ ] Qubit and ancilla counts
- [ ] Raw and transpiled circuit depth
- [ ] One- and two-qubit operation counts
- [ ] State-preparation complexity
- [ ] Shot sensitivity
- [ ] Noise sensitivity
- [ ] Reconstruction fidelity and error
- [ ] Reproducible benchmark report

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
- **v0.2:** Exact QRDA implementation
- **v0.3:** FRQA and comparative audio benchmark
- **v0.4:** FRQI and NEQR
- **v0.5:** Audio/image resource and noise benchmark report
