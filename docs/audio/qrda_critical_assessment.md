# QRDA — Concise Critical Assessment

## Purpose

QRDA is treated here as a **validated quantum-audio foundation**, not as the final research objective.

The repository has already validated its state representation, amplitude/time-register structure, signed/unsigned preprocessing, primary-paper example, reconstruction, logical preparation, representative scaling, finite-shot behavior, and controlled noise behavior.

No additional QRDA-specific operation is required unless a downstream information-hiding experiment later needs it.

## Information model

QRDA stores quantized audio amplitudes as computational-basis values associated with computational-basis time indices.

This gives a clear digital structure for sample-addressed modification and extraction.

## Signed-data limitation

The validated QRDA core is unsigned. Signed classical samples are translated to unsigned values before encoding and translated back after reconstruction.

This is explicit and reproducible, but the quantum state does not directly preserve the bipolar signed structure of the original waveform.

That limitation is the main reason to compare QRDA with FRQA.

## Local addressability and modification

The time register allows operations to target selected sample positions through controlled logic.

This is useful for location-aware information hiding, but the control cost grows with the time-register width. A logically simple local modification may therefore become expensive after decomposition.

## Reversibility

The repository already validates exact reconstruction in its controlled ideal examples. This makes QRDA a suitable baseline for reversible embedding/extraction studies.

Later security experiments should measure **incremental degradation and overhead caused by the embedding method**, rather than re-validating the entire QRDA baseline.

## Circuit cost

Existing results show that qubit count alone is not a sufficient implementation metric. Relevant contributors include:

- time-register control width;
- number of written amplitude bits;
- multi-controlled operations;
- transpiled depth;
- entangling-gate count.

Future QRDA-based security methods should therefore report incremental embedding overhead at the appropriate abstraction level.

## Logical versus transpiled interpretation

The repository distinguishes:

1. quantum-state equivalence;
2. logical preparation equivalence;
3. basis-gate decomposition after transpilation.

The paper's logical controlled-write count must not be interpreted as the final transpiled CX count.

## Finite shots and noise

The repository already contains finite-shot and controlled-noise evidence sufficient for QRDA's current role as a baseline.

Future work should distinguish exact/statevector correctness, finite-shot extraction, and noisy extraction, without repeating a separate QRDA benchmark campaign.

## Suitability for quantum information hiding

### Useful properties

- explicit sample/time association;
- basis-encoded amplitude values;
- reversible baseline reconstruction;
- controlled access to selected locations;
- intuitive digital-audio interpretation.

### Restrictive properties

- unsigned core amplitude representation;
- signed-data offset preprocessing;
- multi-controlled preparation/modification cost;
- increasing circuit depth with longer signals;
- finite-shot extraction requirements;
- sensitivity of deep decomposed circuits to noise.

## Current conclusion

QRDA is a useful baseline for **discrete, sample-addressed quantum information hiding**, but it should not become a large standalone subproject.

Its main value now is as a reference point for the next question:

> **Does direct signed-amplitude representation provide a more natural foundation for audio modification and information hiding than QRDA's unsigned core plus offset preprocessing?**

That question is addressed next with a minimal FRQA baseline.

## Stop decision

**QRDA baseline status: complete for the current research purpose.**

Further QRDA work is deferred unless a downstream experiment requires a specific operation.

Next path:

**FRQA minimal comparison → FRQI/NEQR foundations → representation suitability → quantum information hiding → QML-assisted security analysis → quantum steganalysis.**
