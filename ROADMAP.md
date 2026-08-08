# Research Roadmap

This repository follows a research path from **validated quantum signal representations** to **secure quantum multimedia processing**, with a final emphasis on **quantum steganography, quantum steganalysis, and secure quantum medical imaging**.

Published representation methods are treated as **research baselines**, not as the final objective of the repository. A representation is implemented only to the depth needed to:

1. reproduce and validate the primary literature;
2. expose practical and conceptual limitations;
3. compare representation suitability for downstream security tasks; and
4. support the transition to original research in secure quantum multimedia.

## Research principles

- **Primary-source first:** implementation claims must be traceable to the original paper or clearly identified as repository-side engineering choices.
- **Validation before extension:** state definition, preparation, decoding, reconstruction, and representative resource behavior must be checked before proposing extensions.
- **Critical assessment over feature completeness:** implementing every operation described in a representation paper is not a project goal.
- **Security relevance:** further implementation is prioritized only when it informs watermarking, steganography, steganalysis, secure multimedia, or medical-image research.
- **Reproducibility:** scripts, configurations, seeds, generated artifacts, and negative results should remain reproducible.
- **Claim discipline:** simulator results, transpiled circuits, noisy simulations, and real-QPU execution must be distinguished explicitly. Quantum advantage is not claimed without direct evidence.

---

## Phase 1 — Validated quantum-audio foundation

### 1. QRDA baseline

QRDA is the first fully validated audio-representation baseline.

#### Completed

- [x] Mathematical QRDA state definition
- [x] Unsigned amplitude and time registers
- [x] State-preparation circuit
- [x] Exact statevector validation
- [x] Shot-based simulation
- [x] Decoding and reconstruction
- [x] Resource metrics
- [x] Controlled signal-length and amplitude-resolution scaling
- [x] Sparse, repeated-random, and dense loading profiles
- [x] Raw and basis-transpiled depth, size, and CX accounting
- [x] Shot-sensitivity analysis
- [x] Exact full-coverage probability and theoretical shot thresholds
- [x] Synthetic-noise evaluation
- [x] Calibration-derived hardware-noise evaluation
- [x] QRDA-specific public API
- [x] Arbitrary-length QRDA $2^l$-box implementation
- [x] Redundant/padding-state support
- [x] Correct $L=1$ handling
- [x] Signed-to-unsigned and unsigned-to-signed preprocessing
- [x] Exact reproduction of the primary paper's 15-sample worked example
- [x] Independent reference-state construction
- [x] State-fidelity validation
- [x] Logical preparation-protocol comparison
- [x] Validation of the paper's 33 controlled amplitude writes
- [x] Open/closed-control mapping to Qiskit `mcx`
- [x] Separation of logical operation counts from transpiled CX counts
- [x] Reproducible QRDA visual-validation package
- [x] Logical and transpiled circuit visualization
- [x] Visual reconstruction and state-support outputs

#### Critical assessment to consolidate in v0.2.2

- [ ] Document the unsigned-amplitude limitation of the QRDA core representation
- [ ] Document the role and consequences of signed/unsigned offset preprocessing
- [ ] Consolidate state-preparation scaling findings
- [ ] Consolidate finite-shot reconstruction requirements
- [ ] Consolidate noise-sensitivity findings
- [ ] Consolidate logical-vs-transpiled circuit interpretation
- [ ] Produce a QRDA suitability assessment for downstream security tasks
- [ ] Identify which QRDA properties are useful or restrictive for steganography and steganalysis

#### Deferred unless required by downstream research

The following operations are **not mandatory milestones**. They should be implemented only if a later security or medical-imaging experiment requires them.

- QRDA connection operation
- QRDA mixing operation
- QRDA DPCM compression
- QRDA MBE / combined compression
- Real-QPU execution and mitigation studies

---

## Phase 2 — Selected quantum-audio representation baselines

The goal is **comparison**, not exhaustive reproduction of every published audio representation.

### 2. FRQA — prioritized baseline

FRQA is prioritized because its signed-amplitude treatment provides a direct comparison point with the unsigned QRDA core.

- [ ] Review and cite the primary paper
- [ ] Formalize register and signed-amplitude conventions
- [ ] Implement a minimal independent encoder
- [ ] Implement inverse reconstruction
- [ ] Reproduce at least one published or paper-derived example
- [ ] Add exact statevector validation
- [ ] Add shot-based reconstruction validation
- [ ] Visualize the logical circuit
- [ ] Compare qubit requirements with QRDA
- [ ] Compare state-preparation complexity with QRDA
- [ ] Compare signed-data handling with QRDA
- [ ] Assess suitability for security-oriented signal modification

### 3. QPAM / SQPAM — selective baseline

Implement only if probability-amplitude encoding adds meaningful contrast for the later security analysis.

- [ ] Review and cite the primary papers
- [ ] Decide whether QPAM, SQPAM, or both are required
- [ ] Implement the minimum reproducible baseline
- [ ] Validate decoding and reconstruction
- [ ] Analyze shot dependence
- [ ] Compare local sample accessibility with basis-style audio representations
- [ ] Assess suitability for embedding and steganalysis

### Audio baseline stop rule

A quantum-audio representation is considered sufficiently covered when the repository has:

1. primary-paper grounding;
2. mathematical/register definition;
3. minimal independent implementation;
4. encoding/decoding validation;
5. at least one reproducible visual circuit;
6. a small controlled resource or measurement analysis;
7. a limitations section; and
8. an explicit security-suitability assessment.

Further paper-specific operations are optional.

---

## Phase 3 — Selected quantum-image representation foundations

This phase creates only the image-representation foundation required for later steganography, steganalysis, and medical-image experiments.

### Priority methods

- [ ] FRQI
- [ ] NEQR
- [ ] QPIE / amplitude encoding only if it adds useful comparison value

### Required baseline work

- [ ] Review and cite primary papers
- [ ] Formalize position and intensity/color registers
- [ ] Implement minimal independent encoders
- [ ] Validate reconstruction on small grayscale images
- [ ] Add small medical-image examples
- [ ] Visualize representative circuits
- [ ] Measure qubit, ancilla, depth, and entangling-gate requirements
- [ ] Evaluate local pixel/intensity accessibility
- [ ] Evaluate representation sensitivity to controlled modifications
- [ ] Document suitability for security-oriented image processing

---

## Phase 4 — Representation suitability for quantum multimedia security

This phase is the bridge from published representations to the project's original security research.

### Cross-representation criteria

- [ ] Signed vs unsigned data handling
- [ ] Location of information: basis value, probability amplitude, phase, or mixed form
- [ ] Local addressability of samples or pixels
- [ ] Cost of controlled local modification
- [ ] Required ancillas
- [ ] Raw and transpiled circuit depth
- [ ] Entangling-gate exposure
- [ ] Measurement and reconstruction cost
- [ ] Noise sensitivity
- [ ] Reversibility and extraction fidelity
- [ ] Payload embedding surfaces
- [ ] Detectability of embedding-induced changes
- [ ] Suitability for steganography
- [ ] Suitability for watermarking
- [ ] Suitability for steganalysis
- [ ] Suitability for medical-image integrity constraints

### Main output

- [ ] Reproducible representation-security suitability matrix
- [ ] Evidence-backed recommendation of representations for downstream experiments
- [ ] Explicit rejection/deprioritization of unsuitable representation families

---

## Phase 5 — Quantum steganography and watermarking

This phase marks the transition from representation benchmarking to the main secure-multimedia research program.

- [ ] Review selected primary quantum-steganography and watermarking papers
- [ ] Reproduce a small number of representative baselines
- [ ] Define cover, payload, embedding, extraction, and attack models
- [ ] Implement reproducible embedding/extraction pipelines
- [ ] Measure payload capacity
- [ ] Measure extraction fidelity
- [ ] Measure cover/stego state or image distortion
- [ ] Measure circuit/resource overhead
- [ ] Evaluate robustness under controlled attacks and noise
- [ ] Compare representations using identical security tasks
- [ ] Identify limitations that motivate original embedding methods

---

## Phase 6 — Quantum steganalysis

This is a primary original-research direction of the repository.

- [ ] Define cover-vs-stego threat models
- [ ] Build controlled cover/stego datasets
- [ ] Identify amplitude-, phase-, distribution-, and circuit-sensitive descriptors
- [ ] Establish classical and quantum-aware baselines
- [ ] Develop reproducible quantum steganalysis experiments
- [ ] Evaluate detection accuracy, ROC-AUC, precision/recall, and calibration where appropriate
- [ ] Perform ablation studies
- [ ] Evaluate payload-size sensitivity
- [ ] Evaluate noise and attack sensitivity
- [ ] Analyze whether representation choice changes steganalysis difficulty
- [ ] Develop original security-oriented methods only after strong baselines are established

---

## Phase 7 — Secure quantum medical imaging

Medical imaging is treated as a high-value application domain, not merely another representation demo.

- [ ] Encode small controlled medical-image examples
- [ ] Preserve diagnostically relevant image structure during security operations
- [ ] Evaluate quantum watermarking/steganography for medical-image integrity and provenance
- [ ] Evaluate steganalysis on medical-image representations
- [ ] Measure image fidelity and task-relevant degradation
- [ ] Evaluate attack and noise robustness
- [ ] Compare quantum and size-matched classical baselines where meaningful
- [ ] Separate simulated feasibility from any real-hardware claim

---

## Cross-cutting reproducibility and benchmarking

- [x] Reusable resource-scaling utilities
- [x] Deterministic benchmark profiles and seeds
- [x] Raw and basis-transpiled circuit metrics
- [x] QRDA shot-sensitivity baseline
- [x] QRDA synthetic-noise baseline
- [x] QRDA calibration-derived hardware-noise baseline
- [ ] Unified experiment metadata across representation families
- [ ] Common reconstruction/fidelity metrics
- [ ] Common security-task metrics
- [ ] Machine-readable experiment summaries
- [ ] Reproducible figures for major research milestones
- [ ] Negative-result and limitation reporting

---

## Release targets

- **v0.1:** Unsigned amplitude/time audio foundation
- **v0.1.1:** Controlled resource-scaling benchmark
- **v0.1.2:** Shot-sensitivity and full-coverage benchmark
- **v0.1.3:** Controlled synthetic-noise benchmark
- **v0.1.4:** Calibration-derived hardware-noise benchmark
- **v0.2:** QRDA state-representation formalization
- **v0.2.1:** Complete QRDA $2^l$-box core, primary-paper validation, and visual validation
- **v0.2.2:** QRDA limitations and security-suitability assessment
- **v0.3:** FRQA baseline and signed-audio comparison
- **v0.4:** Selected quantum-image representation baselines, prioritizing FRQI and NEQR
- **v0.5:** Cross-representation security-suitability benchmark
- **v0.6:** Quantum steganography / watermarking baselines
- **v0.7:** Quantum steganalysis baseline and research framework
- **v0.8:** Secure quantum medical-image experiments

---

## What is explicitly not a goal

This repository is **not** intended to:

- implement every operation from every quantum signal-representation paper;
- reproduce every representation proposed in the literature;
- maximize circuit count for its own sake;
- imply that simulator success demonstrates hardware feasibility;
- claim quantum advantage without controlled evidence.

The representation layers exist to support the central research question:

> **Which quantum signal and image representations provide a scientifically defensible foundation for secure quantum multimedia processing, especially steganography, steganalysis, and medical-image security?**
