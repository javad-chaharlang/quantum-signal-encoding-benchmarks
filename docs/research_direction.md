# Research Direction

## Mission

The repository is evolving from a collection of reproducible quantum signal-encoding experiments into a research platform for **secure quantum multimedia processing**.

The central trajectory is:

**validated representation → critical suitability analysis → quantum steganography/watermarking → quantum steganalysis → secure quantum medical imaging**

Published representations remain essential, but they serve as **validated baselines and experimental substrates**, not as the final research objective.

## Why this direction

Quantum audio and image representations define where classical information is placed inside a quantum state and how that information can be addressed, modified, measured, and reconstructed.

Those design choices directly affect later security tasks:

- where a hidden payload can be embedded;
- whether local samples or pixels can be modified efficiently;
- whether changes appear in basis values, amplitudes, phases, or distributions;
- how easily hidden modifications can be extracted;
- how embedding changes may be detected;
- how noise and transpilation alter security behavior;
- and whether medically important image information can be preserved.

For this reason, representation research in this repository is evaluated not only for encoding correctness but also for **downstream security suitability**.

## QRDA as the first validated baseline

QRDA established the repository's validation workflow:

- mathematical state definition;
- register conventions;
- independent implementation;
- exact primary-paper reproduction;
- logical circuit validation;
- visual circuit inspection;
- state/reconstruction checks;
- resource scaling;
- finite-shot behavior;
- synthetic and calibration-derived noise analysis.

The QRDA work also exposed limitations that are important for downstream research.

### 1. Unsigned core representation

The QRDA encoder stores unsigned quantized amplitudes. Signed audio is handled through a separate offset transformation before encoding and an inverse transformation after reconstruction.

This is valid for round-trip reconstruction, but it means that signed-signal semantics are not intrinsic to the QRDA amplitude register. This distinction matters when later security operations manipulate encoded amplitudes directly.

### 2. State-preparation cost

The present explicit loading strategy relies on controlled amplitude writes. The repository's scaling experiments show that qubit count alone does not describe preparation cost; time-register control width and the number of loaded amplitude bits materially affect depth and entangling-gate exposure.

### 3. Finite-shot reconstruction

For ideal QRDA measurement, exact reconstruction requires sufficient coverage of time indices. This turns measurement budget into a practical reconstruction constraint.

### 4. Noise exposure

Larger preparation circuits accumulate more gate exposure, so noise sensitivity must be considered together with representation and loading complexity.

### 5. Logical vs physical circuits

A logical circuit reproduced from a paper must not be confused with a particular transpiled decomposition. Symbolic controlled-write counts and backend-oriented CX counts answer different questions.

These observations are not reasons to reject QRDA. They make QRDA useful as a **critical baseline** against which other representations can be judged.

## Baseline stop rule

A published representation does not need exhaustive implementation.

A baseline is considered sufficient when the repository has:

1. primary-paper citation and terminology;
2. mathematical/register definition;
3. minimal independent encoder;
4. decoding or inverse reconstruction;
5. exact or controlled validation;
6. at least one visual circuit;
7. a small resource/measurement analysis;
8. documented limitations; and
9. an explicit assessment of relevance to downstream security tasks.

Additional paper-specific operations are implemented only when they are needed for a later experiment.

## Decision gates for future representations

Before investing in a new audio or image representation, the project asks:

1. Does it add a genuinely different information-encoding mechanism?
2. Does it solve or illuminate a limitation of an existing baseline?
3. Does it alter local addressability or modification cost?
4. Does it provide a useful embedding surface for security research?
5. Does it change measurement or reconstruction constraints?
6. Does it improve relevance to steganography, steganalysis, watermarking, or medical imaging?

If the answer is mostly no, the representation can be documented without becoming a full implementation milestone.

## Planned research path

### A. Selected audio baselines

FRQA is the next priority because its signed-amplitude treatment provides a direct comparison with QRDA.

QPAM/SQPAM are secondary and should be implemented only if probability-amplitude encoding provides meaningful contrast for security analysis.

### B. Selected image baselines

FRQI and NEQR are prioritized to create the foundation required for image-based security experiments. Other image representations are included only when they add a distinct property needed for comparison.

### C. Representation-security suitability

Audio and image methods will be compared using security-relevant criteria such as:

- signed/unsigned handling;
- basis/amplitude/phase information location;
- local addressability;
- controlled modification cost;
- ancilla requirements;
- depth and entangling gates;
- measurement cost;
- noise sensitivity;
- reversibility;
- payload embedding options;
- embedding detectability;
- medical-image fidelity constraints.

### D. Quantum steganography and watermarking

The project will reproduce a small number of representative published methods, then use those baselines to identify limitations and motivate original secure-embedding research.

### E. Quantum steganalysis

Steganalysis is a central research direction. The project will study whether hidden quantum modifications can be detected from state-, measurement-, phase-, distribution-, or circuit-sensitive evidence and how detection difficulty changes across representations.

### F. Secure quantum medical imaging

Medical images provide a high-value application domain where security operations must be evaluated together with image fidelity and preservation of diagnostically relevant information.

## Scientific claim policy

Repository outputs should distinguish:

- exact mathematical/state results;
- ideal simulator results;
- finite-shot simulator results;
- synthetic-noise results;
- calibration-derived noise-model results;
- transpiler-dependent circuit metrics;
- real-QPU results, when available.

No result should be described as quantum advantage, real-time capability, or practical hardware superiority without direct controlled evidence.

## Research outputs

The project is expected to produce several kinds of outputs:

- reproducible code and tests;
- primary-paper validation notes;
- machine-readable benchmark results;
- visual circuit and reconstruction assets;
- critical representation comparisons;
- security-suitability matrices;
- steganography/steganalysis baselines;
- original research experiments;
- technical LinkedIn posts that communicate each verified milestone without overstating the evidence.

See [`linkedin_research_series.md`](linkedin_research_series.md) for the communication plan.
