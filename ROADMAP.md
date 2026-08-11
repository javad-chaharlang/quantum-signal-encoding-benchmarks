# Research Roadmap

This repository uses quantum audio and image representations as **validated foundations**, not as the final research destination.

The project is organized around three broad technical themes:

- **Quantum Audio & Imaging**
- **Quantum Information Processing**
- **Quantum Machine Learning**

> **Project rule:** do not continue implementing or benchmarking a representation after it has provided the evidence needed for downstream research.

## Research trajectory

**Validated representations → representation suitability → quantum information hiding → quantum machine learning → quantum steganalysis → secure quantum medical imaging**

The repository prioritizes critical understanding and transition to original research over exhaustive reproduction of every operation in representation papers.

---

## Phase 1 — Minimal validated quantum-audio foundations

### QRDA — completed baseline

QRDA is the first validated quantum-audio baseline in the repository.

Completed work already includes the state definition, amplitude/time registers, arbitrary-length encoding, signed/unsigned preprocessing, primary-paper reproduction, reconstruction, state fidelity, logical/transpiled circuit interpretation, representative resource scaling, shot sensitivity, controlled noise analysis, and reproducible figures.

### QRDA closure

No additional QRDA operations are required now.

Deferred unless a later information-hiding experiment specifically needs them:

- connection;
- mixing;
- DPCM compression;
- MBE / combined compression;
- further hardware-oriented experiments.

The QRDA baseline and its concise critical assessment are complete.

See `docs/audio/qrda_critical_assessment.md`.

### FRQA — minimal comparison baseline

FRQA is included only as the second audio foundation required to compare direct signed-amplitude handling with QRDA.

Required:

- [x] primary-paper grounding;
- [x] amplitude/time register definition;
- [x] two's-complement signed-amplitude definition;
- [x] minimal independent encoder;
- [x] inverse reconstruction;
- [x] one validated example;
- [x] state validation;
- [x] one readable logical-circuit figure;
- [x] concise QRDA/FRQA comparison;
- [x] local-modification and information-hiding assessment.

Not required unless downstream research needs them:

- exhaustive reproduction of FRQA signal operations;
- large resource-scaling campaigns;
- separate shot/noise benchmark suites;
- implementation of every operation from the original paper.

### Audio stop rule

After QRDA and FRQA, no additional audio representation is added unless it contributes a meaningfully different information model required by later research.

---

## Phase 2 — Minimal quantum-image foundations

Only the image representations required for information hiding, steganalysis, and medical-imaging research are implemented.

### FRQI

- [x] primary-paper grounding;
- [ ] minimal encoder;
- [ ] small grayscale example;
- [ ] reconstruction/observable validation;
- [ ] one representative logical circuit;
- [ ] pixel-information location analysis;
- [ ] local-modification assessment.

### NEQR

- [x] primary-paper grounding;
- [ ] minimal encoder;
- [ ] small grayscale example;
- [ ] exact intensity reconstruction;
- [ ] one representative logical circuit;
- [ ] pixel-addressability analysis;
- [ ] local-modification assessment.

### Image stop rule

FRQI and NEQR are sufficient as the initial image foundations. Other representations are added only when they provide a necessary capability that these two do not provide.

---

## Phase 3 — Representation Suitability Analysis

This phase is intentionally compact. Its purpose is selection, not another large benchmark campaign.

For each selected representation, record:

- information location;
- signed-data handling;
- sample/pixel addressability;
- local controlled modification;
- reversibility;
- extraction requirements;
- measurement dependence;
- circuit overhead;
- entangling-gate exposure;
- compatibility with information hiding;
- compatibility with quantum machine learning;
- likely value for steganalysis.

Main output:

- [ ] concise representation-suitability matrix;
- [ ] justified selection of downstream representation(s);
- [ ] explicit rejection/deferment of representations that add no useful capability.

---

## Phase 4 — Quantum Information Hiding

This is the first major specialist research phase.

Scope:

- quantum steganography;
- quantum watermarking;
- secure quantum data embedding;
- reversible payload extraction;
- representation-aware embedding.

Core tasks:

- [ ] define cover, payload, stego, embedding, and extraction models;
- [ ] select representation(s) from Phase 3;
- [ ] reproduce only a small number of relevant baselines;
- [ ] implement reproducible embedding/extraction pipelines;
- [ ] measure payload capacity and extraction fidelity;
- [ ] measure cover/stego distortion;
- [ ] measure incremental circuit overhead;
- [ ] evaluate controlled attacks/noise where meaningful;
- [ ] identify limitations motivating original methods.

---

## Phase 5 — Quantum Machine Learning for Security-Oriented Signal Analysis

QML is introduced only when it serves a concrete signal-security task.

Scope may include quantum feature extraction, quantum kernels, variational classifiers, and QCNN-style models where justified.

Principles:

- [ ] retain classical baselines;
- [ ] keep model complexity proportionate to data scale;
- [ ] separate simulation claims from hardware claims;
- [ ] use ablation and representation-dependence analysis where useful.

---

## Phase 6 — Quantum Steganalysis

This is a primary original-research direction.

- [ ] define cover-vs-stego threat models;
- [ ] build controlled cover/stego datasets;
- [ ] identify representation-sensitive observables/descriptors;
- [ ] establish classical and quantum-aware baselines;
- [ ] develop QML-based steganalysis experiments;
- [ ] evaluate accuracy, ROC-AUC, precision, recall, and calibration where appropriate;
- [ ] perform ablation studies;
- [ ] evaluate payload-size, representation, and noise sensitivity;
- [ ] develop original methods after strong baselines are established.

---

## Phase 7 — Secure Quantum Medical Imaging

Medical imaging is treated as an application domain for the mature information-hiding and steganalysis framework.

- [ ] encode small controlled medical-image examples;
- [ ] preserve diagnostically relevant structure;
- [ ] evaluate integrity/provenance watermarking;
- [ ] evaluate secure information hiding and steganalysis;
- [ ] measure image fidelity and task-relevant degradation;
- [ ] evaluate controlled robustness;
- [ ] compare with appropriate classical baselines;
- [ ] separate simulated feasibility from real-hardware claims.

---

## Release targets

- **v0.2.1** — QRDA validated baseline ✅
- **v0.2.2** — Concise QRDA critical assessment
- **v0.3** — Minimal FRQA baseline + QRDA/FRQA comparison
- **v0.4** — Minimal FRQI + NEQR image foundations
- **v0.5** — Representation Suitability Matrix
- **v0.6** — Quantum Information Hiding baselines
- **v0.7** — Quantum Machine Learning for security-oriented signal analysis
- **v0.8** — Quantum Steganalysis framework
- **v0.9** — Secure Quantum Medical Imaging experiments

## What is explicitly not a goal

This repository is not intended to:

- implement every quantum audio or image representation;
- reproduce every operation in every representation paper;
- create large benchmark suites when concise validation is sufficient;
- treat representation engineering as the final research contribution;
- imply hardware feasibility from ideal simulation;
- claim quantum advantage without controlled evidence.

> **Central question:** Which quantum information representations and processing strategies provide the most defensible foundation for information hiding, quantum machine learning, steganalysis, and secure medical imaging?
